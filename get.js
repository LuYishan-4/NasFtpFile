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
       
        const remoteStream = await client.downloadToStream(req.params.filename);
        archive.append(remoteStream, { name: req.params.filename });

        
        archive.file('extra/promo_video.mp4', { name: 'bonus_video.mp4' });

        await archive.finalize();
    } catch (err) {
        res.status(500).send("傳輸錯誤");
    }
    client.close();
});

app.listen(3000);