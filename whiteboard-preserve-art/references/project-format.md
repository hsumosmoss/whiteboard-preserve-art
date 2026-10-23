# 原圖版共用專案格式

使用Python 3.9+的標準函式庫即可執行 `scripts/check_project.py`，無需Codex、專屬API或其他技能。此腳本初始化／檢查清單、來源校驗與路徑幾何，**不渲染影片、不檢查實際畫質**。初始化：

```bash
python scripts/check_project.py init my-project
python scripts/check_project.py hash my-project/sources/source.png
python scripts/check_project.py check my-project
```

`project.json` 結構如下。各數字是格式示例，須填入真實圖片尺寸、hash及時間；資料不代表已取得素材。

```json
{
  "route":"preserve", "stage":"production",
  "duration":36, "timing_basis":"measured",
  "canvas":{"width":1920,"height":1080,"fps":30},
  "deliverables":["video","ebook"],
  "assets":[{
    "id":"scene-art", "source":"sources/source.png",
    "source_sha256":"填入實際64位SHA256", "source_size":[1672,941],
    "crop":[10,52,551,469], "reveal_file":"paths/scene-art.json"
  }],
  "scenes":[{"id":"S1","start":0,"end":5,"items":[
    {"asset_id":"scene-art","start":0.2,"duration":3.5,"x":430,"y":75,"width":1060}
  ]}],
  "cues":[{"start":0.2,"end":3.8,"text":"實際旁白字幕"}],
  "chapters":[], "ebook_pages":[],
  "outputs":[]
}
```

遮罩JSON使用裁切圖本地坐標：

```json
{"width":541,"height":417,"paths":[{"points":[[10,30],[200,30]],"brush_width":32}]}
```

這只是有效格式，不足以覆蓋示例整圖；實際必須依畫面建立足夠路徑並檢視覆蓋。

stage可用draft／planned／production／complete。init建立draft，不冒充已完成素材。非draft需有合法畫布、正片長與場景。source_size須由讀圖取得；腳本只檢查其宣告與crop邊界，真正像素尺寸由Agent另行核對。每個來源hash由原始副本計算，檢查失敗需找原因，不可更新hash掩蓋未授權改圖。

素材經素材關卡生成（見topic-to-assets.md）時，asset加`"origin":"generated"`並記錄生成prompt與重生成次數；手部素材另記素材庫登記（nib本地座標、SHA-256）。生成圖與外部提供圖一律複製入`sources/`再引用。

場景start/end是全片絕對秒數；item.start/duration是幕內相對時間。單筆繪製預設不可重疊，必要多筆配置明寫multiple_pens:true。文字與手部可另記labels／hand；手部包含file及nib本地座標，Agent必須依實作檢視其變換。

chapters項目含id、title、targets（video／ebook）；ebook_pages含type（cover／chapter／content）、chapter_id。電子書章節第一個內容頁前應有相應獨立章節頁，影片章節頁作正式場景計時。

outputs項目含kind及path。complete時所選deliverables需有非空輸出；有配音同步影片以measured時間為準，無音版用audio_status:unavailable和limitations說明。所有檔案路徑相對專案根目錄；來源先複製到專案再引用。
