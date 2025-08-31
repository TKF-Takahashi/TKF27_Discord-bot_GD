<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Auth_hook {

	public function check_login()
	{
		$CI =& get_instance();
		$class = $CI->router->fetch_class();

		if ($class === 'auth') {
			return;
		}
		
		if ( ! isset($CI->session))
		{
			 $CI->load->library('session');
		}

		// --- ここから確認コード ---
		echo "<pre>";
		echo "--- Auth_hook.php (遷移後の画面) ---<br>";
		echo "現在のセッションデータ:<br>";
		var_dump($CI->session->all_userdata());
		echo "</pre>";
		exit; // 確認のためここで処理を停止
		// --- ここまで ---

		if ( ! $CI->session->userdata('is_logged_in'))
		{
			redirect('auth/login');
		}
	}
}