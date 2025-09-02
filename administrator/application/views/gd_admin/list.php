<table id="recruits-table">
    <thead>
        <tr>
            <th class="col-id">ID</th>
            <th class="col-datetime">日時</th>
            <th class="col-place">場所</th>
            <th class="col-message">メッセージ</th>
            <th class="col-industry">業界</th>
            <th class="col-users">参加者/メンター</th>
            <th class="col-status">状態</th>
            <th class="col-actions">操作</th>
        </tr>
    </thead>
    <tbody>
        <?php foreach ($recruits as $recruit): ?>
        <tr>
            <td><?php echo $recruit['id']; ?></td>
            <td><?php echo html_escape($recruit['date_s']); ?></td>
            <td><?php echo html_escape($recruit['message']); ?></td>
            <td><?php echo html_escape($recruit['place']); ?></td>
            <td><?php echo html_escape($recruit['industry']); ?></td>
            <td>
                <?php
                $p_ids = json_decode($recruit['participants'], true) ?: [];
                $m_ids = json_decode($recruit['mentors'], true) ?: [];
                
                if (!empty($p_ids)) {
                    echo '<b>参加者:</b><br>';
                    foreach($p_ids as $id) { echo '<span class="user-tag" data-userid="'.trim($id).'">'.($users[trim($id)] ?? trim($id)).'</span> '; }
                }
                
                if (!empty($m_ids)) {
                    echo '<br><b>メンター:</b><br>';
                    foreach($m_ids as $id) { echo '<span class="user-tag" data-userid="'.trim($id).'">'.($users[trim($id)] ?? trim($id)).'</span> '; }
                }
                ?>
            </td>
            <td>
                <?php echo $recruit['is_deleted'] ? '削除' : '有効'; ?>
            </td>
            <td class="action-buttons">
                <a href="<?php echo site_url('gd_admin/edit/'.$recruit['id']); ?>" class="btn btn-primary">編集</a>
                <a href="<?php echo site_url('gd_admin/delete/'.$recruit['id']); ?>" class="btn btn-danger" data-confirm="本当にこの募集を削除しますか？この操作は元に戻せません。">削除</a>
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
        const userId = tag.dataset.userid;
        // テキストが数字のみ（IDのまま）の場合にリストに追加
        if (/^\d+$/.test(tag.textContent)) {
            userIdsToFetch.add(userId);
        }
    });

    if (userIdsToFetch.size > 0) {
        const ids = Array.from(userIdsToFetch).join(',');
        fetch(`<?php echo site_url('gd_admin/fetch_discord_users'); ?>?ids=${ids}`)
            .then(response => {
                if (!response.ok) { throw new Error('Network response was not ok'); }
                return response.json();
            })
            .then(data => {
                if (data && typeof data === 'object' && !data.error) {
                    userTags.forEach(tag => {
                        const userId = tag.dataset.userid;
                        if (data[userId]) {
                            tag.textContent = data[userId];
                        }
                    });
                }
            })
            .catch(error => console.error('Error fetching user names:', error));
    }
});
</script>