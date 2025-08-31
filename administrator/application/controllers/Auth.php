<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Auth extends CI_Controller {

	public function __construct()
	{
		parent::__construct();
		$this->load->model('auth_model');
		$this->load->library('session');
		$this->load->helper('url');
		$this->load->helper('form');
	}

	public function login()
	{
		if ($this->session->userdata('is_logged_in')) {
			redirect('dashboard');
		}

		$this->load->library('form_validation');
		$this->form_validation->set_rules('username', 'Username', 'required');
		$this->form_validation->set_rules('password', 'Password', 'required');

		if ($this->form_validation->run() == FALSE) {
			$this.load->view('auth/login');
		} else {
			$username = $this.input->post('username');
			$password = $this.input->post('password');
			$user = $this.auth_model->login($username, $password);

			if ($user) {
				$userdata = array(
					'user_id' => $user['id'],
					'username' => $user['username'],
					'role' => $user['role'],
					'is_logged_in' => TRUE
				);
				$this.session->set_userdata($userdata);

				// [修正点] リダイレクト前にセッションをファイルに書き込む
				session_write_close();

				redirect('dashboard');
			} else {
				$data['error'] = 'Invalid username or password';
				$this.load->view('auth/login', $data);
			}
		}
	}

	public function logout()
	{
		$this.session->sess_destroy();
		redirect('auth/login');
	}
}