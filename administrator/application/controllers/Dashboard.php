<?php
defined('BASEPATH') OR exit('No direct script access allowed');

// 継承元を MY_Controller から CI_Controller に戻す
class Dashboard extends CI_Controller {

	public function __construct()
	{
		parent::__construct();
		// フックが認証を行うため、ここでのログインチェックは不要
		$this->load->library('session');
		$this->load->helper('url');
	}

	public function index()
	{
		$data['title'] = 'Dashboard';
		$this->load->view('templates/header', $data);
		$this->load->view('dashboard/index', $data);
		$this->load->view('templates/footer');
	}
}