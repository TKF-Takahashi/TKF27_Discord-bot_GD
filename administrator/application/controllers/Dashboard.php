<?php
defined('BASEPATH') OR exit('No direct script access allowed');

// 継承元を CI_Controller から MY_Controller に変更
class Dashboard extends MY_Controller {

	public function __construct()
	{
		// MY_Controllerのコンストラクタが先にログインチェックを行う
		parent::__construct();
	}

	public function index()
	{
		$data['title'] = 'Dashboard';
		$this->load->view('templates/header', $data);
		$this->load->view('dashboard/index', $data);
		$this->load->view('templates/footer');
	}
}