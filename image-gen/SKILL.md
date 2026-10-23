---
name: 圖片生成 Image Gen
description: 用 OpenAI 生成圖片（gpt-image-1 / dall-e-3）。當使用者要求生圖、生成圖片、畫一張圖、做插圖、出圖、視覺素材、image generation，或需要把文字描述變成圖片時使用。附屬腳本 scripts/gen_image.py，金鑰讀環境變數 OPENAI_API_KEY。
---

# 圖片生成（image-gen）

透過附屬腳本呼叫 OpenAI Images API 生圖。

## 前提

- 金鑰來自環境變數 `OPENAI_API_KEY`（Windows 使用者層級，已設定於本機）。
- **不得**要求使用者提供金鑰，不得把金鑰寫入檔案、指令或對話。

## 流程

1. 從使用者訊息取出提示詞（prompt）。若描述過於籠統（缺主題／風格／用途），先用一句話確認再執行。
2. 依使用者指定決定輸出路徑；未指定時放在當前專案 `output/` 目錄，檔名用主題的英文短詞。
3. 以**技能基底目錄**（載入本技能時提供的 base directory）為基準執行：

   ```powershell
   python "<技能基底目錄>/scripts/gen_image.py" --prompt "提示詞" --out "<輸出路徑>.png" --size 1024x1024
   ```

4. 成功會輸出 `[image-gen] OK: <路徑>`，用 read 工具把圖片展示給使用者。
5. 失敗時依錯誤訊息排查（見下方表格），修好後重跑**同一條指令**（不改动使用者的提示詞）。

## 參數

| 參數 | 預設 | 說明 |
|---|---|---|
| `--prompt` | （必填） | 圖片描述 |
| `--out` | `output.png` | 輸出路徑（自動建立資料夾） |
| `--size` | `1024x1024` | `1024x1024` / `1536x1024` / `1024x1536` / `auto` |
| `--model` | `gpt-image-1` | 也可 `dall-e-3`（依帳戶權限） |
| `--quality` | （不帶） | gpt-image-1：`low` / `medium` / `high` / `auto` |
| `--ref` | （不帶） | 一或多張參考圖路徑；帶參考時改走 `images.edit`，用於風格／主體一致性 |
| `--transparent` | 關 | 透明背景（僅 gpt-image-1） |

## 一致性與無文字原則

- 多張元件需風格一致時：先生成一張「基準圖」定調，後續每張以 `--ref 基準圖.png` 生成，並沿用同一組風格描述。
- 需要透明底的元素（手部、疊加插畫）加 `--transparent`。
- 白板／影片素材 prompt 應明文禁止圖內出現文字與字母；文字由後期圖層加入。生成後逐張放大目視檢查，發現圖內文字即重生成（同一元件最多 3 次，仍失敗則回報卡關）。

## 規則

- 預設 `gpt-image-1` + `1024x1024`；使用者沒特別說就不要追問。
- 一次要多張：逐張執行，檔名加 `_1.png`、`_2.png`……
- 費用意識：測試用預設品質；高畫質或大圖先與使用者確認。
- 不覆蓋既有檔案，除非使用者明確要求。

## 常見錯誤

| 錯誤訊息 | 處理 |
|---|---|
| `OPENAI_API_KEY is not set` | 請使用者在自己的終端機執行 `[Environment]::SetEnvironmentVariable("OPENAI_API_KEY","sk-...","User")` 並重啟 OpenCode。**不得代為設定或索取金鑰。** |
| `No module named 'openai'` | 執行 `pip install openai` |
| `401 / invalid_api_key` | 金鑰無效或已撤銷，請使用者到 platform.openai.com 檢查 |
| `429 / rate limit` | 等待後重試一次；仍失敗則回報使用者 |
| `insufficient_quota` | 帳戶餘額不足，回報使用者儲值 |
| `TypeError: process() takes no keyword arguments` | httpx2 解壓相容問題：`pip install --upgrade brotli`（需 ≥1.2） |
