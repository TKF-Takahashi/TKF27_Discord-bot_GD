<!DOCTYPE html>
<html lang="ja">
<head>
	<meta charset="UTF-8">
	<title>設定</title>
	<style>
		body { font-family: sans-serif; }
		.form-group { margin-bottom: 15px; }
		label { display: block; margin-bottom: 5px; }
		input[type="text"] { width: 300px; padding: 8px; }
	</style>
</head>
<body>
	<h1>設定</h1>
	<?php echo form_open('gd_admin/settings'); ?>
		<div class="form-group">
			<label for="mentor_role_id">メンターロールID</label>
			<input type="text" name="mentor_role_id" value="<?php echo htmlspecialchars($mentor_role_id, ENT_QUOTES, 'UTF-8'); ?>">
		</div>
		<button type="submit">保存</button>
		<a href="<?php echo site_url('gd_admin'); ?>">キャンセル</a>
	<?php echo form_close(); ?>
</body>
</html>