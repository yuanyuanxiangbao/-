import os
import pandas as pd
import json
from pathlib import Path
import logging

# 配置日志记录
logging.basicConfig(filename='preprocessing_errors.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def safe_json_parse(json_str):
    """安全解析JSON字符串，处理格式异常"""
    try:
        if pd.isna(json_str):
            return []
        corrected = json_str.replace("'", "\"").encode('utf-8').decode('unicode_escape')
        return json.loads(corrected)
    except Exception as e:
        logging.error(f"JSON解析失败: {e}\n原始内容: {json_str}")
        return []

def load_and_merge_data(input_folder, main_file):
    """加载主表并合并所有关联表，统一movie_id类型为Int64"""
    input_path = Path(input_folder)
    main_file_path = input_path / main_file
    
    if not main_file_path.exists():
        raise FileNotFoundError(f"主文件 {main_file} 不存在于 {input_folder}")
    
    # 读取主表
    df_main = pd.read_csv(main_file_path, low_memory=False)
    
    # 转换movie_id为Int64（兼容NaN）
    df_main['movie_id'] = pd.to_numeric(df_main['movie_id'], errors='coerce').astype('Int64')
    
    # 清理无效movie_id的行（可选）
    invalid_ids = df_main[df_main['movie_id'].isna()]
    if not invalid_ids.empty:
        print(f"删除无效movie_id的行数: {len(invalid_ids)}")
        df_main = df_main.dropna(subset=['movie_id'])
    
    # 合并关联表
    related_files = [f for f in os.listdir(input_folder) if f.endswith('.csv') and f != main_file]
    
    for rel_file in related_files:
        rel_file_path = input_path / rel_file
        if not rel_file_path.exists():
            print(f"警告: 关联文件 {rel_file} 不存在，跳过合并。")
            continue
        
        try:
            # 读取关联表
            df_rel = pd.read_csv(rel_file_path, low_memory=False)
            
            # 转换movie_id为Int64（兼容NaN）
            if 'movie_id' in df_rel.columns:
                df_rel['movie_id'] = pd.to_numeric(df_rel['movie_id'], errors='coerce').astype('Int64')
            elif 'id' in df_rel.columns:
                df_rel.rename(columns={'id': 'movie_id'}, inplace=True)
                df_rel['movie_id'] = pd.to_numeric(df_rel['movie_id'], errors='coerce').astype('Int64')
            else:
                print(f"警告: 关联文件 {rel_file} 缺少 movie_id 或 id 列，跳过合并。")
                continue
            
            # 合并关联表
            df_main = pd.merge(df_main, df_rel, on="movie_id", how="left")
        
        except Exception as e:
            print(f"错误: 在合并文件 {rel_file} 时发生错误: {e}")
            logging.error(f"在合并文件 {rel_file} 时发生错误: {e}")
    
    return df_main

def preprocess_data(df):
    """预处理数据集，确保必要字段存在，并添加新的字段 genres_score"""
    required_columns = ['genres', 'production_companies', 'movie_id', 'revenue']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"缺少必要的字段: {missing_columns}")
    
    # 处理genres字段
    df['genres'] = df['genres'].apply(safe_json_parse)
    
    # 计算genres_score
    if 'genres' in df.columns:
        # 展平所有genres并统计影响力
        genres_flat = df.apply(lambda row: [(g['name'], row['revenue']) for g in row['genres']], axis=1).explode()
        genre_stats = pd.DataFrame(genres_flat.tolist(), columns=['genre', 'revenue']).groupby('genre')['revenue'].agg(['sum', 'count'])
        genre_stats['influence'] = genre_stats['sum'] / genre_stats['count']
        
        # 计算每部电影的genres_score
        def calculate_genres_score(genres):
            if not genres:
                return 0
            return sum(genre_stats.loc[g['name'], 'influence'] for g in genres if g['name'] in genre_stats.index) / len(genres)
        
        df['genres_score'] = df['genres'].apply(calculate_genres_score)
    
    return df

def main():
    # 定义输入和输出文件夹路径
    input_folder = r"D:\太虚山\统计建模\数据集\CSV"
    output_folder = r"D:\太虚山\统计建模\数据集\已处理数据集"
    
    # 使用Path对象构建路径
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    
    # 确保输出文件夹存在
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 主文件名
    main_filename = 'cleaned_movies.csv'
    
    try:
        # 加载并合并数据
        df_merged = load_and_merge_data(input_path, main_filename)
        
        # 打印前几行数据用于调试
        print("First few rows of merged data:")
        print(df_merged.head())
        
        # 预处理数据
        df_processed = preprocess_data(df_merged)
        
        # 构造输出文件路径
        output_filepath = output_path / f'processed_{main_filename}'
        
        # 保存处理后的数据到指定路径
        df_processed.to_csv(output_filepath, index=False)
        
        # 输出前5行数据作为示例
        print(f"Processed and saved to {output_filepath}")
        print(df_processed.head())
    except Exception as e:
        print(f"Error during processing: {e}")
        logging.error(f"Error during processing: {e}")

if __name__ == "__main__":
    main()



