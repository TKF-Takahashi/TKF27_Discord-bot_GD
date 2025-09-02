<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Welcome extends CI_Controller {
	public function index()
	{
		// 管理画面のTOPにリダイレクト
		redirect('gd_admin');
	}
}