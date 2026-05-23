import os
import pandas as pd

# 定义输入文件路径
input_file = r'D:\太虚山\统计建模\数据集\CSV\movies.csv'

# 检查文件是否存在
if not os.path.exists(input_file):
    print(f"文件 {input_file} 不存在。")
else:
    # 读取CSV文件
    try:
        df = pd.read_csv(input_file, encoding='ISO-8859-1', low_memory=False)
        
        # 获取所有列名
        columns = set(df.columns)
        
        # 打印所有列名
        print("文件中的列名:")
        for col in sorted(columns):
            print(col)
        
        # 必需的列
        required_columns = {
            'id', 'title', 'belongs_to_collection', 'homepage', 'genres',
            'original_language', 'overview', 'popularity', 'poster_path',
            'production_companies', 'production_countries', 'release_date',
            'revenue', 'runtime', 'status', 'vote_average', 'vote_count'
        }
        
        # 检查缺失的列
        missing_columns = required_columns - columns
        if missing_columns:
            print("\n缺少的列:")
            for col in sorted(missing_columns):
                print(col)
        else:
            print("\n所有必需的列都存在。")
            
    except Exception as e:
        print(f"读取文件时发生错误: {e}")



