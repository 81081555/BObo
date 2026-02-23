# 猜数字（4 位）对战规则与实现

现在项目提供 **H5 + PWA** 可分享对战版本：

- 可创建房间并生成分享链接（`/room/<房间号>`），直接发给微信好友加入。
- 手机浏览器可直接玩，并支持安装为 PWA。
- 双方加入后按回合提交 4 位猜测，支持红/绿模式与可选黄色提示。
- 使用 commit/reveal（secret + nonce 哈希）机制防作弊。

## 启动

后端入口文件是项目根目录的 `app.py`：

```bash
python app.py
```

默认监听 `0.0.0.0:8000`。
如部署平台要求固定端口（否则可能被网关判定为 502），可通过环境变量覆盖：

```bash
HOST=0.0.0.0 PORT=8080 python app.py
```

浏览器访问 `http://localhost:8000`（或你设置的端口）。

## 测试

```bash
python -m unittest discover -s tests -v
```


> 若直接打开分享链接，服务器会回退到前端入口页（SPA fallback），避免出现 404。
