# Careerbot Local Note 導入・利用マニュアル（職員向け）

面談を録音すると、**あなたのPCの中だけで**文字起こし・相談記録の下書き・面談の振り返りを作るツールです。
このマニュアルは、パソコンにあまり詳しくない方でも進められるように書いています。黒い画面（ターミナル／PowerShell）に打ち込む文は、すべて**コピーして貼り付けるだけ**で動きます。

---

## 0. はじめに読んでください

### できること
- 面談を録音して文字起こし（日本語）
- カウンセラーと学生の発言を自動で分ける（目安。手で直せます）
- キャリアセンターの相談記録の形に要約
- カウンセラー自身のための振り返り（深掘りできた点・次回聞くこと）
- ZoomやTeamsの録音ファイル（m4a / mp3 / wav）からも作れます

### できないこと・約束
- **相談内容は一切外部に送られません**。インターネット上のAIは使いません
- 利用料はかかりません
- **無償・無保証・個別サポートなし**です。困ったときは本書の「7. よくあるエラー」を見てください
- 相談記録の保管・削除・持ち出しは、所属大学の規程に従ってください
- **録音前に学生の同意を得てください**（「記録作成のためにAIで文字起こしします」と伝える）

### 所要時間
初回セットアップ：30〜60分（ダウンロード待ちが大半）。2回目以降は起動30秒。

---

## 1. 準備するもの

| | 推奨 | 最低 |
|---|---|---|
| PC | Mac（Apple Silicon：M1〜M4） | Mac（Intel）／Windows 11（動作未確認） |
| メモリ | 16GB以上 | 8GB |
| 空き容量 | 15GB | 6GB |
| ブラウザ | Google Chrome | Microsoft Edge でも可 |
| 権限 | ソフトをインストールできること | |

**メモリの確認方法**
- Mac：画面左上のリンゴ → 「このMacについて」→「メモリ」
- Windows：スタートを右クリック → 「システム」→「実装RAM」

大学貸与PCで「インストールには管理者の許可が必要」と出る場合は、情報システム部門に `docs/SECURITY.md`（情シス向け説明）を添えて相談してください。

---

## 2. Macでのセットアップ

### 手順1：Ollama（AIの実行ソフト）を入れる
1. https://ollama.com を開き「Download for macOS」
2. ダウンロードしたzipを開き、Ollamaをアプリケーションフォルダに移動して起動
3. 画面上部のメニューバーにラマのアイコンが出ればOK

### 手順2：ターミナルを開く
- Launchpad →「その他」→「ターミナル」（またはSpotlight（⌘＋スペース）で「ターミナル」と検索）
- 黒または白の文字だけの画面が開きます。以降、この画面に貼り付けます

### 手順3：AIモデルを取得する
メモリ **16GB以上** の方はこちらを貼ってEnter（約10GB・10〜20分）：
```
ollama pull gemma4:e4b
```
メモリ **8GB** の方はこちら（約3.3GB）：
```
ollama pull gemma3:4b
```
`success` と出れば完了です。

### 手順4：Pythonが入っているか確認する
```
python3 --version
```
`Python 3.10` 以上の数字が出ればOK。
「command not found」か、3.9以下、または「開発ツールをインストールしますか」と聞かれた場合は「今はしない」を押し、https://www.python.org/downloads/ から「Download Python 3.12」を入れてください（インストーラーは全部「続ける」でOK）。入れ終わったらターミナルを一度閉じて開き直し、もう一度上の1行で確認します。

### 手順5：ツールをダウンロードして起動する
下の5行を**まとめて**コピーして貼り付け、Enter：
```
cd ~/Downloads
curl -L -o lnote.zip https://github.com/KojiOkazaki/careerbot-local-note/archive/refs/heads/main.zip
unzip -q -o lnote.zip -d ~/Documents
cd ~/Documents/careerbot-local-note-main
chmod +x start.command && ./start.command
```
「初回セットアップ中」と表示されて数分待ちます。終わると自動でChromeが開きます。

**2回目以降の起動**：Finderで「書類」→「careerbot-local-note-main」→ `start.command` をダブルクリック。
「開発元を確認できないため開けません」と出たら、右クリック →「開く」を選びます。

---

## 3. Windowsでのセットアップ（動作未確認・自己責任）

### 手順1：PowerShellを開く
スタートボタンを右クリック →「ターミナル」または「Windows PowerShell」。青い（または黒い）文字だけの画面が開きます。

### 手順2：PythonとOllamaを入れる
下の2行を貼り付けてEnter。途中で「同意しますか」と出たら `Y` を押します。
```
winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
winget install --id Ollama.Ollama -e --accept-source-agreements --accept-package-agreements
```
終わったら **PowerShellを一度閉じて、開き直します**（開き直さないと次の手順で「見つかりません」になります）。

`winget` が使えない古いWindowsの場合は、https://www.python.org/downloads/（インストール画面で **「Add python.exe to PATH」に必ずチェック**）と https://ollama.com からそれぞれインストールしてください。

### 手順3：Ollamaを起動し、AIモデルを取得する
スタートメニューから「Ollama」を起動（タスクバー右下にアイコンが出ます）。その後PowerShellで、
メモリ **16GB以上**：
```
ollama pull gemma4:e4b
```
メモリ **8GB**：
```
ollama pull gemma3:4b
```

### 手順4：ツールをダウンロードして起動する
下の4行をまとめて貼り付けてEnter（日本語のユーザー名でも動くよう `C:\LocalNote` に置きます）：
```
Invoke-WebRequest -Uri https://github.com/KojiOkazaki/careerbot-local-note/archive/refs/heads/main.zip -OutFile $env:TEMP\lnote.zip
Expand-Archive -Path $env:TEMP\lnote.zip -DestinationPath C:\LocalNote -Force
Set-Location C:\LocalNote\careerbot-local-note-main
.\start.bat
```
「初回セットアップ中」と表示されて数分待ちます。「WindowsによってPCが保護されました」と出たら「詳細情報」→「実行」。
終わると自動でブラウザが開きます。開かない場合は Chrome で `http://127.0.0.1:8765` を開いてください。

**2回目以降の起動**：エクスプローラーで `C:\LocalNote\careerbot-local-note-main` を開き、`start.bat` をダブルクリック。

---

## 4. 初回起動後の確認

Chromeの画面左「準備の確認」を見ます。

| 表示 | 意味 |
|---|---|
| ✓ Ollama：接続済み | AIの実行ソフトが動いている |
| ✓ LLM：gemma4:e4b | 要約に使うモデルが入っている |
| ✗ 文字起こし：（初回に自動取得） | **正常です**。初回の文字起こし時に約1.5GBを自動取得します |
| ✓ 外部送信：なし | このPC以外に通信しない設計 |
| ✓ 録音音声：文字起こし後に削除 | 音声ファイルは残さない |

✗が「Ollama」や「LLM」に付いている場合は「7. よくあるエラー」へ。

**黒い画面（ターミナル／PowerShell）は閉じないでください。** 閉じるとツールが止まります。使い終わったら閉じて構いません。

---

## 5. 使い方

1. **マイクを選ぶ**（内蔵マイクで構いません）。Chromeが「マイクを使用することを許可しますか」と聞いたら「許可」
2. **カウンセラー名**を入れる（任意。話者の判別精度が上がります）
3. 学生に同意を得て **「録音を開始」**。面談の最初に「カウンセラーの○○です」と名乗ると判別が安定します
4. 面談後 **「録音を止めて文字起こし」**。60分の面談で数分〜十数分待ちます（初回はモデル取得でさらに数分）
5. 文字起こしが出たら **「話者を推定」**。間違いは「カウンセラー／学生」のラベルをクリックして切り替え
6. **「相談記録（要約）」タブ →「相談記録を作成」**
7. **「振り返り」タブ →「振り返りを作成」**（自分のための内省用。評価ではありません）
8. **「Markdownを保存」** でファイルに書き出し、大学の相談記録システムへ転記
9. 転記が終わったら **「この記録を削除」** でPCから消す

### 運用のおすすめ
- AIの出力は必ず自分で確認してから記録にする（聞き取り違い・話者の取り違えは起こります）
- 記録を長くPCに残さない。「転記したら削除」を習慣に
- PCのディスク暗号化（Mac：FileVault／Windows：BitLocker）とログインパスワードを設定する
- Zoom面談は、Zoomの「ローカル録音」で保存したファイルを画面左下「ファイルを選択」から読み込む

### 記録の保存先
- Mac：`ホーム/CareerbotLocalNote/日時のフォルダ`
- Windows：`C:\Users\ユーザー名\CareerbotLocalNote\日時のフォルダ`
中に `transcript.md`（文字起こし）`summary.md`（相談記録）`review.md`（振り返り）が入っています。

---

## 6. 設定を変えたいとき

`config.py` というファイルをメモ帳（Windows）やテキストエディット（Mac）で開いて数字や文字を書き換え、保存してツールを再起動します。

| したいこと | 書き換える行 |
|---|---|
| 別のAIモデルを使う | `LLM_MODEL = "auto"` → `LLM_MODEL = "gemma3:4b"` など（先に `ollama pull` が必要） |
| 文字起こしを速くする（精度は下がる） | `WHISPER_MODEL = "auto"` → `WHISPER_MODEL = "medium"` または `"small"` |
| 録音音声も残す | `SAVE_AUDIO = False` → `SAVE_AUDIO = True` |
| 保存先を変える | `DATA_DIR = ...` の行 |

---

## 7. よくあるエラー

### セットアップ中

**「command not found: python3」「'python' は認識されていません」**
→ Pythonが入っていない、または入れた直後で反映されていない。ターミナル／PowerShellを閉じて開き直す。それでも出なければ python.org からインストール（Windowsは「Add python.exe to PATH」にチェック）。

**「ollama: command not found」「'ollama' は認識されていません」**
→ Ollamaのインストール直後は認識されないことがあります。ターミナル／PowerShellを閉じて開き直す。Ollamaアプリも起動しておく。

**Windowsで `winget` が使えない**
→ Windows 10の古い版です。python.org と ollama.com から手動インストール（手順2の補足）。

**「zsh: permission denied: ./start.command」（Mac）**
→ 実行権限がない。次を貼ってから再度実行：
```
chmod +x ~/Documents/careerbot-local-note-main/start.command
```

**「開発元を確認できないため開けません」（Mac）**
→ start.command を右クリック →「開く」。

**「WindowsによってPCが保護されました」**
→ 「詳細情報」→「実行」。

**「ライブラリのインストールに失敗しました」**
→ 大学のプロキシ（ネット制限）の可能性。情報システム部門にプロキシ設定を確認。一度失敗した場合は、フォルダ内の `.venv` フォルダを削除してから再度 start を実行すると復旧することがあります。

**「Address already in use」「ポート8765」**
→ すでに起動しています。開いている黒い画面を探すか、PCを再起動。

### 起動後・画面の表示

**✗ Ollama：接続できません**
→ Ollamaが起動していない。Mac：アプリケーションからOllamaを起動（メニューバーにアイコン）。Windows：スタートからOllamaを起動（タスクバー右下）。起動後「もう一度確認」。

**✗ LLM：gemma4:e4b（未取得）**
→ モデルが入っていない。黒い画面（またはもう1枚ターミナルを開いて）で：
```
ollama pull gemma4:e4b
```
8GBのPCで `gemma3:4b` を入れたのに ✗ の場合は `config.py` の `LLM_MODEL` を `"gemma3:4b"` に書き換えて再起動。

**マイクが選べない／「マイクの許可が必要です」**
→ Chromeのアドレスバー左のアイコン →「マイク」を許可。Macはさらに「システム設定 → プライバシーとセキュリティ → マイク」でChromeをオン。

### 文字起こし・要約

**文字起こしがとても遅い（60分の面談で30分以上）**
→ PCの性能相応です。`config.py` の `WHISPER_MODEL` を `"medium"` に。

**文字起こしが空、または「音声から発話を検出できませんでした」**
→ マイクの選択違い（別のデバイスを拾っている）。マイクを変えて短く録音し直す。

**「文字起こしに失敗しました」でファイル形式のエラー**
→ 対応していない形式。m4a / mp3 / wav / webm に変換してから読み込む（ZoomのローカルRecordingは m4a で保存されます）。

**「要約に失敗しました」「話者推定に失敗しました」**
→ Ollamaが落ちたか、メモリ不足。他のアプリを閉じる。8〜16GBのPCなら `LLM_MODEL = "gemma3:4b"` に変更。

**話者が全部「不明」または逆になる**
→ 面談の冒頭で名乗る／画面でカウンセラー名を入れる／ラベルをクリックして直す。内蔵マイク1本での判別には限界があります。

**要約に事実と違うことが書かれる**
→ 起こりえます。必ず本文（文字起こし）と照らして修正してから記録にしてください。

### その他

**黒い画面を閉じてしまった**
→ ツールが止まっただけです。start をもう一度ダブルクリック。記録は消えていません。

**アンインストールしたい**
→ ツールのフォルダ（Mac：書類/careerbot-local-note-main、Windows：C:\LocalNote）と、記録フォルダ（CareerbotLocalNote）を削除。Ollamaも不要なら通常のアプリと同様に削除。

---

## 8. 問い合わせについて

本ツールは無償・無保証で、個別のサポートは行っていません。
利用者同士の情報交換は GitHub の Discussions をご利用ください：
https://github.com/KojiOkazaki/careerbot-local-note/discussions

複数職員での運用、タブレット利用、設定・研修・保守が必要な大学向けには有償版があります：https://careerbot.tokyo

---
CAREERBOT Inc. / 東京都立産業技術大学院大学 岡崎浩二
