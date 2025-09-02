<p>データベースに対する操作ログの一覧です。</p>
<table>
    <thead>
        <tr>
            <th>ID</th>
            <th>日時</th>
            <th>ソース</th>
            <th>レベル</th>
            <th>メッセージ</th>
        </tr>
    </thead>
    <tbody>
        <?php foreach ($logs as $log): ?>
        <tr>
            <td><?php echo $log['id']; ?></td>
            <td><?php echo $log['timestamp']; ?></td>
            <td><?php echo html_escape($log['source']); ?></td>
            <td><?php echo html_escape($log['level']); ?></td>
            <td><?php echo nl2br(html_escape($log['message'])); ?></td>
        </tr>
        <?php endforeach; ?>
    </tbody>
</table>