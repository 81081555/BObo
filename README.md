# 猜数字（4 位）对战规则与实现

现在项目提供 **H5 + PWA** 可分享对战版本：

- 可创建房间并生成分享链接，直接发给微信好友加入。
- 手机浏览器可直接玩，并支持安装为 PWA。
- 双方加入后按回合提交 4 位猜测，支持红/绿模式与可选黄色提示。
- 使用 commit/reveal（secret + nonce 哈希）机制防作弊。

## 启动

```bash
python app.py
```

打开 `http://localhost:8000`。

## 测试

```bash
python -m unittest discover -s tests -v
```
