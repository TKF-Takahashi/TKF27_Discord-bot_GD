<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Auth_hook {

	public function check_login()
	{
		$CI =& get_instance();

		// 現在アクセスされているクラス名とメソッド名を取得
		$class = $CI->router->fetch_class();
		$method = $CI->router->fetch_method();

		// ログインコントローラ自体はチェックから除外する
		if ($class === 'auth') {
			return;
		}

		// セッションライブラリがロードされているか確認
		if ( ! isset($CI->session))
		{
			$CI->load->library('session');
		}

		// ログイン状態でない場合、ログインページにリダイレクト
		if ( ! $CI->session->userdata('is_logged_in'))
		{
			redirect('auth/login');
		}
	}
}