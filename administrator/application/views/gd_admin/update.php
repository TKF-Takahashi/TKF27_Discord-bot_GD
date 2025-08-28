<!DOCTYPE html>
<html lang="ja">
<head>
	<meta charset="UTF-8">
	<title>アップデート管理</title>
	<style>
		body { font-family: sans-serif; }
		.container { width: 800px; margin: 0 auto; padding: 20px; }
		.section { margin-bottom: 30px; }
		h2 { border-bottom: 2px solid #ccc; padding-bottom: 5px; }
	</style>
</head>
<body>
	<div class="container">
		<h1>アップデート管理</h1>
		<div class="section">
			<h2>データベースバックアップ</h2>
			<p>現在のデータベースをバックアップファイルとしてダウンロードします。アップデート前に必ず実行してください。</p>
			<a href="<?php echo site_url('gd_admin/backup'); ?>" class="button">データベースをバックアップ</a>
		</div>
		<p><a href="<?php echo site_url('gd_admin'); ?>">管理画面に戻る</a></p>
	</div>
</body>
</html>