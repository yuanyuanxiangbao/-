import os
import pandas as pd
import json
from collections import defaultdict
from datetime import datetime

def preprocess_data(df):
    # Step 1: 处理缺失值与二值变量生成
    df['has_collection'] = df['belongs_to_collection'].apply(lambda x: 0 if pd.isna(x) else 1)
    df['has_homepage'] = df['homepage'].apply(lambda x: 0 if pd.isna(x) else 1)
    df['has_tagline'] = df['tagline'].apply(lambda x: 0 if pd.isna(x) else 1)
    
    # Step 2: JSON字段解析与量化
    
    # genres_score 计算
    genres_dict = defaultdict(float)
    genres_count = defaultdict(int)
    for idx, row in df.iterrows():
        try:
            genres = json.loads(row['genres'].replace("'", "\""))
            for g in genres:
                genres_dict[g['name']] += row['revenue']
                genres_count[g['name']] += 1
        except (json.JSONDecodeError, TypeError):
            continue
    
    for k in genres_dict:
        genres_dict[k] /= genres_count[k] if genres_count[k] > 0 else 1
    
    def parse_genres(json_str, genres_dict):
        try:
            genres_list = json.loads(json_str.replace("'", "\""))
            scores = [genres_dict.get(g['name'], 0) for g in genres_list]
            return sum(scores) / len(scores) if scores else 0
        except (json.JSONDecodeError, TypeError):
            return 0
    
    df['genres_score'] = df['genres'].apply(parse_genres, args=(genres_dict,))
    
    # production_companies 处理
    pr_companies_freq = df['production_companies'].str.extractall(r"'name': '(.*?)'").groupby(0)[0].count().sort_values(ascending=False).head(35).index.tolist()
    df['pr_companies_num'] = df['production_companies'].apply(lambda x: len(json.loads(x.replace("'", "\""))) if isinstance(x, str) else 0)
    for company in pr_companies_freq:
        df[f'company_{company}'] = df['production_companies'].apply(lambda x: int(any(company == comp['name'] for comp in json.loads(x.replace("'", "\"")))) if isinstance(x, str) else 0)
    
    # production_countries 处理
    pr_countries_freq = df['production_countries'].str.extractall(r"'name': '(.*?)'").groupby(0)[0].count().sort_values(ascending=False).head(25).index.tolist()
    df['pr_countries_num'] = df['production_countries'].apply(lambda x: len(json.loads(x.replace("'", "\""))) if isinstance(x, str) else 0)
    for country in pr_countries_freq:
        df[f'country_{country}'] = df['production_countries'].apply(lambda x: int(any(country == cnty['name'] for cnty in json.loads(x.replace("'", "\"")))) if isinstance(x, str) else 0)
    
    # cast 处理
    top_cast_freq = df['cast'].str.extractall(r"'name': '(.*?)'").groupby(0)[0].count().sort_values(ascending=False).head(30).index.tolist()
    df['cast_num'] = df['cast'].apply(lambda x: len(json.loads(x.replace("'", "\""))) if isinstance(x, str) else 0)
    df['has_top_actor'] = df['cast'].apply(lambda x: int(any(actor['name'] in top_cast_freq for actor in json.loads(x.replace("'", "\"")))) if isinstance(x, str) else 0)
    
    # crew 处理
    crew_roles_freq = df['crew'].str.extractall(r"'job': '(.*?)'").groupby(0)[0].count().sort_values(ascending=False).head(30).index.tolist()
    df['crew_num'] = df['crew'].apply(lambda x: len(json.loads(x.replace("'", "\""))) if isinstance(x, str) else 0)
    
    crew_role_influence = defaultdict(float)
    crew_role_count = defaultdict(int)
    for idx, row in df.iterrows():
        try:
            crews = json.loads(row['crew'].replace("'", "\""))
            for c in crews:
                crew_role_influence[c['job']] += row['revenue']
                crew_role_count[c['job']] += 1
        except (json.JSONDecodeError, TypeError):
            continue
    
    for k in crew_role_influence:
        crew_role_influence[k] /= crew_role_count[k] if crew_role_count[k] > 0 else 1
    
    def parse_crew(json_str, crew_role_influence):
        try:
            crews_list = json.loads(json_str.replace("'", "\""))
            scores = [crew_role_influence.get(c['job'], 0) for c in crews_list]
            return sum(scores) / len(scores) if scores else 0
        except (json.JSONDecodeError, TypeError):
            return 0
    
    df['crew_score'] = df['crew'].apply(parse_crew, args=(crew_role_influence,))
    
    # Step 3: 时间字段处理
    def extract_release_info(date_str):
        try:
            date_obj = pd.to_datetime(date_str)
            year = date_obj.year
            quarter = date_obj.quarter
            weekday = date_obj.weekday()
            return year, quarter, weekday
        except (ValueError, OverflowError):
            return pd.NaT, pd.NaT, pd.NaT
    
    df[['release_year', 'release_quarter', 'release_weekday']] = df['release_date'].apply(extract_release_info).apply(pd.Series)
    
    # Step 4: 数值字段处理
    runtime_mode = df['runtime'].mode()[0]
    df['runtime'].fillna(runtime_mode, inplace=True)
    
    # Step 5: 删除冗余字段
    columns_to_drop = ['id', 'imdb_id', 'original_title', 'poster_path', 'overview', 'spoken_languages', 'title',
                       'belongs_to_collection', 'genres', 'homepage', 'production_companies', 'production_countries', 'cast', 'crew', 'tagline', 'release_date']
    df.drop(columns=columns_to_drop, axis=1, inplace=True)
    
    return df

# 定义输入和输出文件夹路径
input_folder = r'D:\太虚山\统计建模\数据集\CSV'
output_folder = r'D:\太虚山\统计建模\数据集\已处理数据集'

# 确保输出文件夹存在
os.makedirs(output_folder, exist_ok=True)

# 遍历输入文件夹中的所有CSV文件
for filename in os.listdir(input_folder):
    if filename.endswith('.csv'):
        filepath = os.path.join(input_folder, filename)
        
        try:
            # 读取数据并进行预处理
            df = pd.read_csv(filepath)
            processed_df = preprocess_data(df)
            
            # 构造输出文件路径
            output_filepath = os.path.join(output_folder, f'processed_{filename}')
            
            # 保存处理后的数据到指定路径
            processed_df.to_csv(output_filepath, index=False)
            
            # 输出前5行数据作为示例
            print(f"Processed and saved {filename} to {output_filepath}")
            print(processed_df.head())
        except Exception as e:
            print(f"Error processing file {filename}: {e}")



