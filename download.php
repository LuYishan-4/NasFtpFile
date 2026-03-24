<?php
// 1. 設定檔案路徑
$mainFile = "ftp_storage/main_project.java"; // 來自 FTP 的主檔案
$extraFile = "assets/readme_v2.pdf";        // 想要強迫多下載的東西
$zipName = "FRC_Package_" . date("Ymd") . ".zip";

// 2. 建立 ZIP 物件
$zip = new ZipArchive();
$tmpFile = tempnam(sys_get_temp_dir(), 'zip'); // 建立暫存檔

if ($zip->open($tmpFile, ZipArchive::CREATE) === TRUE) {
    // 加入主檔案
    if (file_exists($mainFile)) {
        $zip->addFile($mainFile, basename($mainFile));
    }
    
    // 注入「多下載」的東西
    if (file_exists($extraFile)) {
        $zip->addFile($extraFile, "請先閱讀我.pdf");
    }
    
    $zip->close();

    // 3. 設定 Header 讓瀏覽器執行下載
    header('Content-Type: application/zip');
    header('Content-Disposition: attachment; filename="' . $zipName . '"');
    header('Content-Length: ' . filesize($tmpFile));
    
    // 讀取並輸出檔案內容
    readfile($tmpFile);
    
    // 刪除暫存檔
    unlink($tmpFile);
} else {
    echo "無法建立壓縮檔";
}
?>