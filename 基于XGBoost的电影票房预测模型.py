# -*- coding: utf-8 -*-
"""
论文第三章完整复现代码：基于XGBoost的电影票房预测模型
作者：何识了
日期：2023年10月
"""

# ====================== 环境配置 ======================
import sys
import os
import platform

# 自动检测并安装缺失库
required_packages = ['numpy', 'pandas', 'scikit-learn', 'xgboost', 'matplotlib', 'shap']
if not sys.warnoptions:
    import warnings
    warnings.filterwarnings("ignore")

def install_package(package):
    if platform.system() == "Windows":
        os.system(f"{sys.executable} -m pip install {package}")
    else:
        os.system(f"pip3 install {package} --user")

for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"正在安装缺失的包: {package}")
        install_package(package)

# 导入必要的库
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
import shap

# ====================== 数据加载与预处理 ======================

def load_and_preprocess(data_dir):
    """加载并预处理数据（整合前序步骤）"""
    # 定义路径
    input_dir = Path(data_dir) / "raw"
    processed_dir = Path(data_dir) / "processed"
    
    # 加载预处理后的主数据
    try:
        df = pd.read_csv(processed_dir / "processed_cleaned_movies.csv", 
                        parse_dates=['release_date'],
                        dtype={'movie_id': 'Int64'})
    except FileNotFoundError:
        raise ValueError("预处理数据未找到，请先运行预处理脚本")
    
    # 论文中关键特征列表（示例，需根据实际预处理结果调整）
    feature_columns = [
        'budget', 'genres_score', 'has_collection', 'release_year',
        'company_Paramount', 'country_US', 'cast_num', 'crew_score',
        'runtime', 'has_homepage', 'release_quarter', 'lang_en'
    ]
    
    # 确保所有特征存在
    missing_features = [f for f in feature_columns if f not in df.columns]
    if missing_features:
        raise KeyError(f"缺失关键特征: {missing_features}. 请检查预处理步骤")
    
    # 目标变量处理（对数变换）
    df['log_revenue'] = np.log1p(df['revenue'])
    
    return df[feature_columns], df['log_revenue']

# ====================== 时间序列交叉验证 ======================

def temporal_split(X, y, test_years=2):
    """按时间划分训练测试集"""
    # 提取年份信息（假设X中包含release_year）
    years = X['release_year'].values
    split_year = years.max() - test_years
    
    train_idx = np.where(years <= split_year)[0]
    test_idx = np.where(years > split_year)[0]
    
    return (X.iloc[train_idx], X.iloc[test_idx],
            y.iloc[train_idx], y.iloc[test_idx])

# ====================== XGBoost模型构建 ======================

def build_xgb_model(X_train, y_train):
    """模型训练与参数调优"""
    # 初始化基础模型
    model = XGBRegressor(
        objective='reg:squarederror',
        n_jobs=-1,
        random_state=42,
        tree_method='hist'  # 论文中使用精确方法，大数据可改为gpu_hist
    )
    
    # 论文中的参数搜索空间
    param_grid = {
        'learning_rate': [0.01, 0.05, 0.1],
        'max_depth': [3, 5, 7],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.7, 0.8, 1.0],
        'n_estimators': [500, 1000],
        'reg_alpha': [0, 0.1],
        'reg_lambda': [0, 0.1]
    }
    
    # 时间序列交叉验证
    tscv = TimeSeriesSplit(n_splits=3)
    
    # 网格搜索
    grid_search = GridSearchCV(
        estimator=model,
        param_grid=param_grid,
        cv=tscv,
        scoring='neg_mean_squared_error',
        verbose=2,
        n_jobs=-1
    )
    
    print("开始参数搜索...")
    grid_search.fit(X_train.drop(columns=['release_year']), y_train)
    
    return grid_search.best_estimator_

# ====================== 模型评估与可视化 ======================

def evaluate_model(model, X_test, y_test):
    """模型性能评估与可视化"""
    # 预测与指标计算
    y_pred = model.predict(X_test.drop(columns=['release_year']))
    
    # 逆变换获取实际票房
    y_test_actual = np.expm1(y_test)
    y_pred_actual = np.expm1(y_pred)
    
    metrics = {
        'MAE': mean_absolute_error(y_test_actual, y_pred_actual),
        'RMSE': np.sqrt(mean_squared_error(y_test_actual, y_pred_actual)),
        'R2': r2_score(y_test_actual, y_pred_actual)
    }
    
    # 残差分析
    residuals = y_test_actual - y_pred_actual
    plt.figure(figsize=(12, 6))
    sns.histplot(residuals, kde=True, bins=30)
    plt.title("残差分布")
    plt.xlabel("预测误差（美元）")
    plt.savefig('./residual_dist.png', dpi=300)
    
    # 特征重要性
    plt.figure(figsize=(10, 8))
    xgboost.plot_importance(model, max_num_features=20, importance_type='gain')
    plt.title("特征重要性（增益）")
    plt.savefig('./feature_importance.png', dpi=300)
    
    return metrics

# ====================== SHAP解释 ======================

def explain_model(model, X_sample):
    """SHAP解释"""
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    
    # 全局解释
    plt.figure()
    shap.summary_plot(shap_values, X_sample, plot_type="bar")
    plt.savefig('./shap_global.png', dpi=300)
    
    # 单样本解释
    plt.figure()
    shap.plots.waterfall(shap_values[0], max_display=15)
    plt.savefig('./shap_waterfall.png', dpi=300)

# ====================== 主流程 ======================

if __name__ == "__main__":
    # 数据加载
    DATA_DIR = r"D:\太虚山\统计建模\数据集"
    X, y = load_and_preprocess(DATA_DIR)
    
    # 时间序列划分
    X_train, X_test, y_train, y_test = temporal_split(X, y, test_years=2)
    
    # 模型训练
    print("数据维度:", X_train.shape)
    model = build_xgb_model(X_train, y_train)
    
    # 评估
    metrics = evaluate_model(model, X_test, y_test)
    print("\n模型性能:")
    print(f"- MAE: ${metrics['MAE']:,.0f}")
    print(f"- RMSE: ${metrics['RMSE']:,.0f}")
    print(f"- R²: {metrics['R2']:.3f}")
    
    # 解释分析
    explain_sample = X_test.drop(columns=['release_year']).sample(50, random_state=42)
    explain_model(model, explain_sample)
    
    # 保存模型
    model.save_model('./xgboost_model.json')
    print("模型已保存至 xgboost_model.json")

# ====================== 输出说明 ======================

"""
运行结果将生成：
- residual_dist.png: 残差分布直方图
- feature_importance.png: 特征重要性排序
- shap_global.png: 全局特征贡献
- shap_waterfall.png: 单样本解释
- xgboost_model.json: 可部署的模型文件
"""



