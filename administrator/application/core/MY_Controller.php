<?php
defined('BASEPATH') OR exit('No direct script access allowed');

/**
 * すべての認証が必要なコントローラの親クラス
 */
class MY_Controller extends CI_Controller {

    public function __construct()
    {
        parent::__construct();
        $this->load->library('session');
        $this->load->helper('url');

        // ログイン状態でない場合、ログインページにリダイレクト
        if ( ! $this->session->userdata('is_logged_in'))
        {
            redirect('auth/login');
        }
    }

    /**
     * 管理者権限があるかどうかをチェックする
     */
    protected function _check_admin()
    {
        if ($this->session->userdata('role') !== 'admin') {
            show_error('この操作を行う権限がありません。', 403, 'Permission Denied');
            return false;
        }
        return true;
    }
}

/**
 * ログインページなど、認証が不要なコントローラの親クラス
 */
class Public_Controller extends CI_Controller {

    public function __construct()
    {
        parent::__construct();
        $this->load->library('session');
        $this->load->helper('url');
        $this->load->helper('form');
    }
}