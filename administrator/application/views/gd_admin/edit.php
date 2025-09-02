<?php echo validation_errors('<div class="alert alert-danger">', '</div>'); ?>
<?php echo form_open('gd_admin/edit/'.$recruit['id']); ?>

<div class="form-group">
    <label for="date_s">日時 (YYYY/MM/DD HH:MM)</label>
    <input type="text" name="date_s" class="form-control" value="<?php echo set_value('date_s', $recruit['date_s']); ?>">
</div>
<div class="form-group">
    <label for="place">場所</label>
    <input type="text" name="place" class="form-control" value="<?php echo set_value('place', $recruit['place']); ?>">
</div>
<div class="form-group">
    <label for="max_people">最大人数</label>
    <input type="number" name="max_people" class="form-control" value="<?php echo set_value('max_people', $recruit['max_people']); ?>">
</div>
<div class="form-group">
    <label for="industry">業界</label>
    <input type="text" name="industry" class="form-control" value="<?php echo set_value('industry', $recruit['industry']); ?>">
</div>
<div class="form-group">
    <label for="message">メッセージ</label>
    <textarea name="message" class="form-control"><?php echo set_value('message', $recruit['message']); ?></textarea>
</div>
<div class="form-group">
    <label for="participants">参加者ID (カンマ区切り)</label>
    <textarea name="participants" class="form-control"><?php echo set_value('participants', implode(',', json_decode($recruit['participants'], true) ?: [])); ?></textarea>
</div>
<div class="form-group">
    <label for="mentors">メンターID (カンマ区切り)</label>
    <textarea name="mentors" class="form-control"><?php echo set_value('mentors', implode(',', json_decode($recruit['mentors'], true) ?: [])); ?></textarea>
</div>
<div class="form-group form-check">
    <input type="checkbox" name="mentor_needed" value="1" <?php echo set_checkbox('mentor_needed', '1', (bool)$recruit['mentor_needed']); ?>>
    <label>メンター希望</label>
</div>
<div class="form-group form-check">
    <input type="checkbox" name="notification_sent" value="1" <?php echo set_checkbox('notification_sent', '1', (bool)$recruit['notification_sent']); ?>>
    <label>通知済み</label>
</div>

<button type="submit" class="btn btn-success">更新</button>
<a href="<?php echo site_url('gd_admin/list'); ?>" class="btn btn-secondary">キャンセル</a>

<?php echo form_close(); ?>