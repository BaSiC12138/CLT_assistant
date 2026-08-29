# CLT_assistant

CLT 方案小助手桌面应用。

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
