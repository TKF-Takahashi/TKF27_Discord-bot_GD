<!DOCTYPE html>
<html lang="ja">
<head>
	<meta charset="UTF-8">
	<title>募集編集</title>
	<style>
		body { font-family: sans-serif; }
		.form-group { margin-bottom: 15px; }
		label { display: block; margin-bottom: 5px; }
		input[type="text"], textarea { width: 500px; padding: 8px; }
		textarea { height: 100px; }
	</style>
</head>
<body>
	<h1>募集編集 (ID: <?php echo $recruit['id']; ?>)</h1>
	<?php echo form_open('gd_admin/edit/'.$recruit['id']); ?>
		<div class="form-group">
			<label for="date_s">日時</label>
			<input type="text" name="date_s" value="<?php echo htmlspecialchars($recruit['date_s'], ENT_QUOTES, 'UTF-8'); ?>">
		</div>
		<div class="form-group">
			<label for="place">場所</label>
			<input type="text" name="place" value="<?php echo htmlspecialchars($recruit['place'], ENT_QUOTES, 'UTF-8'); ?>">
		</div>
		<div class="form-group">
			<label for="max_people">定員</label>
			<input type="text" name="max_people" value="<?php echo $recruit['max_people']; ?>">
		</div>
		<div class="form-group">
			<label for="note">備考</label>
			<textarea name="note"><?php echo htmlspecialchars($recruit['note'], ENT_QUOTES, 'UTF-8'); ?></textarea>
		</div>
		<div class="form-group">
			<label for="participants">参加者 (JSON形式)</label>
			<textarea name="participants"><?php echo htmlspecialchars($recruit['participants'], ENT_QUOTES, 'UTF-8'); ?></textarea>
		</div>
		<button type="submit">更新</button>
		<a href="<?php echo site_url('gd_admin'); ?>">キャンセル</a>
	<?php echo form_close(); ?>
</body>
</html>