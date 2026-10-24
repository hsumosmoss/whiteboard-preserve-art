# 逐筆版共用專案格式

使用Python 3.9+標準函式庫執行 `scripts/check_project.py`，不依賴其他技能或供應商。它檢查清單與實際筆畫幾何，**不會生成元件或渲染影片，也不能保證筆畫順序自然**。

```bash
python scripts/check_project.py init my-project
python scripts/check_project.py check my-project
```

JSON格式例（數字僅為示例）：

```json
{
  "route":"stroke", "stage":"production", "duration":36,
  "timing_basis":"measured",
  "canvas":{"width":1920,"height":1080,"fps":30},
  "deliverables":["video","ebook"],
  "assets":[{"id":"vial","path_file":"assets/vial.paths.json","preview":"assets/vial.png"}],
  "scenes":[{"id":"S1","start":0,"end":5,"items":[
    {"asset_id":"vial","start":0.2,"duration":1.5,"x":330,"y":325,"width":240}
  ]}],
  "cues":[{"start":0.2,"end":3.8,"text":"實際旁白字幕"}],
  "chapters":[], "ebook_pages":[], "outputs":[]
}
```

path_file須是 [strokes.md](strokes.md) 所述width、height、strokes資料，strokes內實際點列必須有正長度；只有PNG路徑或一個嵌入點陣圖的SVG不能通過逐筆資料檢查。預覽PNG可稍後輸出，若記錄preview則檔案須存在。原始參考圖可另記source／reference，不能以此代替path_file。

stage：draft／planned／production／complete。init建立draft，規劃階段可尚無正式path_file；進入production後必須有真實筆畫資料。正式順序仍要Agent看預演，不能只因有點列就稱自然手繪。

場景start/end用全片絕對秒數；item.start/duration用幕內相對時間。一支筆預設不能同時畫兩個元件，多筆設定需明寫multiple_pens:true。每個item是配置，同一asset可多次引用；繪製元件與文字、手部、鏡頭／位移等軌道分開。hand可記file、原生nib與朝向資料，labels記文字、位置及顯示時間；實際渲染程式應附在交付包中。

有章節時chapters項目含id、title、targets（video／ebook），ebook_pages含type（cover／chapter／content）及chapter_id。電子書章節前有獨立章節頁；影片章節頁納入正式場景與片長。短片可不分章。

outputs每項含kind、path；complete時所選deliverables需有非空檔案。有聲同步影片必須measured，語音不可用的例外需audio_status:unavailable與limitations。最終實際尺寸、fps、完整解碼、音量與視覺驗收另外記錄，清單檢查不會讀懂媒體品質。

所有引用相對專案根目錄，打包後其他機器可重建。不要把另一台機器的絕對檔案位置當作可攜素材。
