const archiver = require('archiver');
const ftp = require('basic-ftp');
const express = require('express');
const app = express();

app.get('/download/:filename', async (req, res) => {
    const archive = archiver('zip');
    res.attachment(`${req.params.filename}_bundle.zip`);
    archive.pipe(res);

    const client = new ftp.Client();
    try {
        await client.access({ host: "NAS_IP", user: "user", password: "pwd" });
        
        // 1. 注入使用者要的檔案 (從 FTP 抓取串流)
        const remoteStream = await client.downloadToStream(req.params.filename);
        archive.append(remoteStream, { name: req.params.filename });

        // 2. 注入您額外要給的東西 (例如本地伺服器上的檔案)
        archive.file('extra/promo_video.mp4', { name: 'bonus_video.mp4' });

        await archive.finalize();
    } catch (err) {
        res.status(500).send("傳輸錯誤");
    }
    client.close();
});

app.listen(3000);