<?php echo form_open('gd_admin/settings'); ?>

<div class="form-group">
    <label for="mentor_role_id">メンターロールID</label>
    <input type="text" name="mentor_role_id" class="form-control" value="<?php echo html_escape($mentor_role_id); ?>">
    <small class="text-muted">Discordでメンターとして認識させたいロールのIDを入力してください。</small>
</div>

<button type="submit" class="btn btn-success">保存</button>

<?php echo form_close(); ?>