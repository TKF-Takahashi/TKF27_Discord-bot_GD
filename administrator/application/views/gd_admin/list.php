<!DOCTYPE html>
<html lang="ja">
<head>
	<meta charset="UTF-8">
	<title>GD募集 管理画面</title>
	<style>
		body { font-family: sans-serif; }
		table { border-collapse: collapse; width: 100%; }
		th, td { border: 1px solid #ddd; padding: 8px; }
		th { background-color: #f2f2f2; }
		.actions a { margin-right: 10px; }
	</style>
</head>
<body>
	<h1>GD募集 管理画面</h1>
	<table>
		<thead>
			<tr>
				<th>ID</th>
				<th>日時</th>
				<th>場所</th>
				<th>定員</th>
				<th>備考</th>
				<th>参加者 (JSON)</th>
				<th>操作</th>
			</tr>
		</thead>
		<tbody>
			<?php foreach ($recruits as $r): ?>
			<tr>
				<td><?php echo $r['id']; ?></td>
				<td><?php echo htmlspecialchars($r['date_s'], ENT_QUOTES, 'UTF-8'); ?></td>
				<td><?php echo htmlspecialchars($r['place'], ENT_QUOTES, 'UTF-8'); ?></td>
				<td><?php echo $r['max_people']; ?></td>
				<td><?php echo htmlspecialchars($r['note'], ENT_QUOTES, 'UTF-8'); ?></td>
				<td><?php echo htmlspecialchars($r['participants'], ENT_QUOTES, 'UTF-8'); ?></td>
				<td class="actions">
					<a href="<?php echo site_url('gd_admin/edit/'.$r['id']); ?>">編集</a>
					<a href="<?php echo site_url('gd_admin/delete/'.$r['id']); ?>" onclick="return confirm('本当に削除しますか？');">削除</a>
				</td>
			</tr>
			<?php endforeach; ?>
		</tbody>
	</table>
</body>
</html>