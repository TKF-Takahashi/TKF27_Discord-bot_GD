<!DOCTYPE html>
<html lang="ja">
<head>
	<meta charset="UTF-8">
	<title><?php echo $title; ?> - Bot Admin</title>
	<link rel="stylesheet" href="<?php echo base_url('assets/css/style.css'); ?>">
</head>
<body>
	<?php $this->load->view('templates/sidebar'); ?>
	<div class="main-content">
		<div class="breadcrumb">
			<a href="<?php echo site_url('dashboard'); ?>">TOP</a>
			<?php if(isset($breadcrumb)): ?>
				<?php echo ' &gt; ' . $breadcrumb; ?>
			<?php endif; ?>
		</div>
		<h1><?php echo $title; ?></h1>