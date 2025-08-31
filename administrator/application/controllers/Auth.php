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
			$this->load->view('auth/login');
		} else {
			$username = $this->input->post('username');
			$password = $this->input->post('password');
			$user = $this->auth_model->login($username, $password);

			if ($user) {
				$userdata = array(
					'user_id' => $user['id'],
					'username' => $user['username'],
					'role' => $user['role'],
					'is_logged_in' => TRUE
				);
				$this->session->set_userdata($userdata);

				// --- ここから確認コード ---
				$session_id = session_id();
				$session_path = APPPATH . 'cache/' . 'ci_admin_session' . $session_id;

				echo "認証成功。";
				echo "次のコマンドで、セッションファイルの中身を確認してください。<br><br>";
				echo "<pre>cat " . $session_path . "</pre>";
				exit; // ここで処理を停止して確認
				// --- ここまで ---

			} else {
				$data['error'] = 'Invalid username or password';
				$this->load->view('auth/login', $data);
			}
		}
	}

	public function logout()
	{
		$this->session->sess_destroy();
		redirect('auth/login');
	}
}