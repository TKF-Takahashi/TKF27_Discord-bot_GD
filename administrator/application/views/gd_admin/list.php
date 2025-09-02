<table id="recruits-table">
    <thead>
        <tr>
            <th class="col-id">ID</th>
            <th class="col-datetime">日時</th>
            <th class="col-place">場所</th>
            <th class="col-message">メッセージ</th>
            <th class="col-industry">業界</th>
            <th class="col-users">参加者/メンター</th>
            <th class="col-status">削除フラグ</th>
            <th class="col-actions">操作</th>
        </tr>
    </thead>
    <tbody>
        <?php foreach ($recruits as $recruit): ?>
        <tr>
            <td class="col-id"><?php echo $recruit['id']; ?></td>
            <td class="col-datetime"><?php echo html_escape($recruit['date_s']); ?></td>
            <td class="col-place"><?php echo html_escape($recruit['place']); ?></td>
            <td class="col-message"><?php echo html_escape($recruit['message']); ?></td>
            <td class="col-industry"><?php echo html_escape($recruit['industry']); ?></td>
            <td class="col-users">
                <?php
                $p_ids = json_decode($recruit['participants'], true) ?: [];
                $m_ids = json_decode($recruit['mentors'], true) ?: [];
                
                if (!empty($p_ids)) {
                    echo '<b>参加者:</b><br>';
                    foreach($p_ids as $id) { echo '<span class="user-tag" data-userid="'.$id.'">' . ($users[$id] ?? $id) . '</span> '; }
                }
                
                if (!empty($m_ids)) {
                    echo '<br><b>メンター:</b><br>';
                    foreach($m_ids as $id) { echo '<span class="user-tag" data-userid="'.$id.'">' . ($users[$id] ?? $id) . '</span> '; }
                }
                ?>
            </td>
            <td class="col-status">
                <?php echo $recruit['is_deleted'] ? '<span style="color:red;">削除済み</span>' : '有効'; ?>
            </td>
            <td class="col-actions action-buttons">
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
        if (tag.textContent === tag.dataset.userid) {
            userIdsToFetch.add(tag.dataset.userid);
        }
    });

    if (userIdsToFetch.size > 0) {
        const ids = Array.from(userIdsToFetch).join(',');
        fetch(`<?php echo site_url('gd_admin/fetch_discord_users'); ?>?ids=${ids}`)
            .then(response => response.json())
            .then(data => {
                if(data){
                    userTags.forEach(tag => {
                        const userId = tag.dataset.userid;
                        if (data[userId]) {
                            tag.textContent = data[userId];
                        }
                    });
                }
            });
    }
});
</script>