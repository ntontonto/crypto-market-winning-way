# Crypto Market Winning Way - Setup Guide

## 自動セットアップ

### Windows
```cmd
setup.bat
```

### Linux/Mac/Git Bash
```bash
chmod +x setup.sh
./setup.sh
```

## セットアップ内容

setup.bat / setup.sh は以下を自動実行します：

1. **Python 3.11の確認** - Python 3.11がインストールされているか確認
2. **仮想環境の作成** - `.venv`ディレクトリを作成（既存の場合は削除して再作成）
3. **pipのアップグレード** - 最新版のpipにアップデート
4. **avのインストール** - プリビルド版のavをインストール（v13.x）
5. **依存関係のインストール** - requirements.txtから全パッケージをインストール
6. **動作確認** - Python と manim のバージョンを表示

## 手動セットアップ（参考）

手動でセットアップする場合は以下の手順：

```cmd
# 1. 仮想環境作成
py -3.11 -m venv .venv

# 2. pipアップグレード
.venv\Scripts\python.exe -m pip install -U pip

# 3. avをインストール（プリビルド版）
.venv\Scripts\python.exe -m pip install "av>=13.0.0,<14.0.0" --only-binary av

# 4. 依存関係をインストール
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 5. 動作確認
.venv\Scripts\python.exe -m manim --version
```

## 要件

- **Python 3.11** が必要です
- Windows の場合、Microsoft Visual C++ Build Tools は不要です（プリビルド版を使用）

## トラブルシューティング

### Python 3.11が見つからない
Python 3.11を https://www.python.org/downloads/ からインストールしてください。

### avのインストールに失敗
setup.batは自動的にプリビルド版（--only-binary）を試みます。失敗した場合でもrequirements.txtから再試行されます。

### manimのバージョン確認
```cmd
.venv\Scripts\python.exe -m manim --version
```

正常にインストールされていれば `Manim Community v0.19.1` のように表示されます。
