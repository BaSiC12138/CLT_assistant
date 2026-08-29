# CLT_assistant

CLT 方案小助手桌面应用。

当前版本：`V1.0.1`

应用启动后会自动检查 GitHub Release。发现新版本时显示中文更新说明，并可在浏览器中下载最新 EXE。

## 运行

```powershell
python -m pip install -r requirements.txt
python app/main.py
```

## 测试

```powershell
$env:PYTHONPATH = "app"
$env:QT_QPA_PLATFORM = "offscreen"
python -m unittest discover -s tests
```
