# 衛星軌跡移除器 (Satellite Trail Remover)

這是一個使用深度學習技術來移除衛星圖像中衛星軌跡的應用程式。該專案結合了前端界面和後端處理服務，能夠自動檢測並移除衛星圖像中的軌跡。

## 功能特點

- 自動檢測衛星圖像中的軌跡
- 使用深度學習模型進行軌跡移除
- 提供友好的 Web 界面
- 支持即時預覽處理結果
- 保存處理前後的圖像對比

## 技術棧

### 前端
- Nuxt.js 3
- Vue 3
- TailwindCSS
- TypeScript

### 後端
- FastAPI
- PyTorch
- OpenCV
- NumPy

## 安裝步驟

### 前端安裝

```bash
# 安裝依賴
npm install

# 開發環境運行
npm run dev

# 構建生產版本
npm run build
```

### 後端安裝

```bash
# 進入後端目錄
cd server

# 安裝 Python 依賴
pip install -r requirements.txt

# 運行後端服務
python main.py
```

## 使用說明

1. 啟動前端服務（默認端口：3000）
2. 啟動後端服務（默認端口：8000）
3. 在瀏覽器中訪問 http://localhost:3000
4. 上傳需要處理的衛星圖像
5. 等待處理完成
6. 查看並下載處理結果

## 目錄結構

```
satellite-trail-remover/
├── server/                 # 後端服務
│   ├── main.py            # 主程序
│   ├── dsr_model.py       # 深度學習模型
│   ├── discrete_model.py  # 離散模型
│   └── data_loader_test.py # 數據加載器
├── pages/                 # 前端頁面
├── assets/               # 靜態資源
├── public/              # 公共文件
└── package.json         # 前端依賴配置
```

## 開發指南

### 代碼規範

```bash
# 運行代碼檢查
npm run lint

# 運行樣式檢查
npm run lint:style

# 運行測試
npm run test
```

### 環境變量

創建 `.env` 文件並添加以下配置：

```env
# 前端配置
NUXT_PUBLIC_API_URL=http://localhost:8000

# 後端配置
MODEL_PATH=./models
UPLOAD_PATH=./uploads
```

## 貢獻指南

1. Fork 本專案
2. 創建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟一個 Pull Request

## 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 文件

## 聯繫方式

如有任何問題或建議，請通過以下方式聯繫：

- 電子郵件：[您的郵箱]
- GitHub：[您的 GitHub 用戶名]

## 致謝

- 感謝所有貢獻者
- 感謝使用的開源項目和庫
