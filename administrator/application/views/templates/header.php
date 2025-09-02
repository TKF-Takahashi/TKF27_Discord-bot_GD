<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title><?php echo $title; ?> - GD Bot Admin</title>
    <link rel="stylesheet" href="<?php echo base_url('assets/css/style.css'); ?>">
</head>
<body>

<div class="sidebar">
    <h2>GD Bot Admin</h2>
    <ul>
        <li class="<?php echo ($this->uri->segment(2) == '' || $this->uri->segment(2) == 'index') ? 'active' : ''; ?>">
            <a href="<?php echo site_url('gd_admin'); ?>">TOP</a>
        </li>
        <li class="<?php echo ($this->uri->segment(2) == 'list') ? 'active' : ''; ?>">
            <a href="<?php echo site_url('gd_admin/list'); ?>">募集一覧</a>
        </li>
        <li class="<?php echo ($this->uri->segment(2) == 'settings') ? 'active' : ''; ?>">
            <a href="<?php echo site_url('gd_admin/settings'); ?>">設定</a>
        </li>
        <li class="<?php echo ($this->uri->segment(2) == 'logs') ? 'active' : ''; ?>">
            <a href="<?php echo site_url('gd_admin/logs'); ?>">操作ログ</a>
        </li>
        <li class="<?php echo ($this->uri->segment(2) == 'backup') ? 'active' : ''; ?>">
            <a href="<?php echo site_url('gd_admin/backup'); ?>">バックアップ</a>
        </li>
    </ul>
</div>

<div class="main-content">
    <header>
        <h1><?php echo $title; ?></h1>
    </header>

    <div class="breadcrumb">
        <a href="<?php echo site_url('gd_admin'); ?>">TOP</a> &gt; <?php echo $title; ?>
    </div>

    <?php if ($this->session->flashdata('success')): ?>
        <div class="alert alert-success">
            <?php echo $this->session->flashdata('success'); ?>
        </div>
    <?php endif; ?>
    <?php if ($this->session->flashdata('error')): ?>
        <div class="alert alert-danger">
            <?php echo $this->session->flashdata('error'); ?>
        </div>
    <?php endif; ?>

    <div class="container"></div>