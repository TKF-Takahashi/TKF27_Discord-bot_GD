<div class="container">
	<h2><?php echo $title; ?></h2>

	<?php if ($this->session->flashdata('success')): ?>
		<div class="alert alert-success" role="alert">
			<?php echo $this->session->flashdata('success'); ?>
		</div>
	<?php endif; ?>

	<?php echo form_open('gd_admin/settings'); ?>
		<div class="form-group">
			<label for="channel_id">チャンネルID</label>
			<input type="text" class="form-control" name="channel_id" id="channel_id" value="<?php echo html_escape($channel_id); ?>">
		</div>
		<div class="form-group">
			<label for="mentor_role_id">メンターロールID</label>
			<input type="text" class="form-control" name="mentor_role_id" id="mentor_role_id" value="<?php echo html_escape($mentor_role_id); ?>">
		</div>
		<div class="form-group">
			<label for="admin_role_id">管理者ロールID</label>
			<input type="text" class="form-control" name="admin_role_id" id="admin_role_id" value="<?php echo html_escape($admin_role_id); ?>">
		</div>
		<button type="submit" class="btn btn-primary">保存</button>
	</form>
</div>