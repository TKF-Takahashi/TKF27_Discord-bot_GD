<table id="recruits-table">
    <thead>
        <tr>
            <th>ID</th>
            <th>日時</th>
            <th>場所</th>
            <th>業界</th>
            <th>参加者/メンター</th>
            <th>状態</th>
            <th>操作</th>
        </tr>
    </thead>
    <tbody>
        <?php foreach ($recruits as $recruit): ?>
        <tr>
            <td><?php echo $recruit['id']; ?></td>
            <td><?php echo html_escape($recruit['date_s']); ?></td>
            <td><?php echo html_escape($recruit['place']); ?></td>
            <td><?php echo html_escape($recruit['industry']); ?></td>
            <td>
                <?php
                $p_ids = json_decode($recruit['participants'], true) ?: [];
                $m_ids = json_decode($recruit['mentors'], true) ?: [];
                echo '<b>参加者:</b> ' . count($p_ids) . '名<br>';
                foreach($p_ids as $id) { echo '<span class="user-tag" data-userid="'.$id.'">' . ($users[$id] ?? $id) . '</span> '; }
                echo '<br><b>メンター:</b> ' . count($m_ids) . '名<br>';
                foreach($m_ids as $id) { echo '<span class="user-tag" data-userid="'.$id.'">' . ($users[$id] ?? $id) . '</span> '; }
                ?>
            </td>
            <td>
                <?php echo $recruit['is_deleted'] ? '<span style="color:red;">削除済み</span>' : '有効'; ?><br>
                <?php echo $recruit['notification_sent'] ? '通知済み' : '未通知'; ?>
            </td>
            <td class="action-buttons">
                <a href="<?php echo site_url('gd_admin/edit/'.$recruit['id']); ?>" class="btn btn-primary">編集</a>
                <a href="<?php echo site_url('gd_admin/delete/'.$recruit['id']); ?>" class="btn btn-danger" data-confirm="本当にこの募集を削除しますか？この操作は元に戻せません。">物理削除</a>
            </td>
        </tr>
        <?php endforeach; ?>
    </tbody>
</table>

<script>
document.addEventListener("DOMContentLoaded", function() {
    const userTags = document.querySelectorAll('.user-tag');
    const userIdsToFetch = new Set();
    userTags.forEach(tag => {
        // もしユーザー名がIDと同じ（つまり未取得）なら取得リストに追加
        if (tag.textContent === tag.dataset.userid) {
            userIdsToFetch.add(tag.dataset.userid);
        }
    });

    if (userIdsToFetch.size > 0) {
        const ids = Array.from(userIdsToFetch).join(',');
        fetch(`<?php echo site_url('gd_admin/fetch_discord_users'); ?>?ids=${ids}`)
            .then(response => response.json())
            .then(data => {
                userTags.forEach(tag => {
                    const userId = tag.dataset.userid;
                    if (data[userId]) {
                        tag.textContent = data[userId];
                    }
                });
            });
    }
});
</script>