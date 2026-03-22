<?php
// download_bundle.php
$requestedFile = $_GET['file']; // 使用者想下載的主檔案
$extraFile = "assets/important_notice.pdf"; // 強制附帶的檔案

$zip = new ZipArchive();
$zipName = "download_package_" . time() . ".zip";

if ($zip->open($zipName, ZipArchive::CREATE) === TRUE) {
    // 1. 從 FTP 或本地 NAS 路徑加入主檔案
    $zip->addFile("ftp_storage/" . $requestedFile, $requestedFile);
    
    // 2. 加入您想「多下載」的東西
    $zip->addFile($extraFile, "READ_ME_FIRST.pdf");
    
    $zip->close();

    // 3. 推送給瀏覽器下載
    header('Content-Type: application/zip');
    header('Content-disposition: attachment; filename='.$zipName);
    header('Content-Length: ' . filesize($zipName));
    readfile($zipName);
    
    // 下載後刪除暫存的 ZIP
    unlink($zipName);
}
?>