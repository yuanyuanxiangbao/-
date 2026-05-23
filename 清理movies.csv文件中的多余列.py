import os
import pandas as pd

# 定义输入和输出文件路径
input_file = r'D:\太虚山\统计建模\数据集\CSV\movies.csv'
output_file = r'D:\太虚山\统计建模\数据集\CSV\cleaned_movies.csv'

# 检查文件是否存在
if not os.path.exists(input_file):
    print(f"文件 {input_file} 不存在。")
else:
    # 读取CSV文件
    try:
        df = pd.read_csv(input_file, encoding='ISO-8859-1', low_memory=False)
        
        # 删除所有 Unnamed: 开头的列
        columns_to_drop = [col for col in df.columns if col.startswith('Unnamed:')]
        df.drop(columns=columns_to_drop, inplace=True)
        
        # 保存清理后的文件
        df.to_csv(output_file, index=False)
        
        print(f"清理后的文件已保存到 {output_file}")
        
        # 打印清理后的列名
        print("清理后的列名:")
        for col in sorted(df.columns):
            print(col)
            
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
