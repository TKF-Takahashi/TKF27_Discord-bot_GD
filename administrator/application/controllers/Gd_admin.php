<?php
defined('BASEPATH') OR exit('No direct script access allowed');

// 継承元を MY_Controller から CI_Controller に戻す
class Gd_admin extends CI_Controller {

	public function __construct()
	{
		parent::__construct();
		// フックがログインチェックを行う
		$this->load->library('session');
		$this->load->helper('url');
		$this->load->model('recruit_admin_model');
		$this->load->helper('form');
		$this->load->helper('download');
	}

	// 権限チェック関数をここに戻す
	private function _check_admin()
	{
		if ($this->session->userdata('role') !== 'admin') {
			show_error('You do not have permission to access this page.', 403);
			return false;
		}
		return true;
	}

	public function index()
	{
		$data['title'] = '募集一覧';
		$data['breadcrumb'] = '募集一覧';
		$data['recruits'] = $this->recruit_admin_model->get_all_recruits();

		$this->load->view('templates/header', $data);
		$this->load->view('gd_admin/list', $data);
		$this->load->view('templates/footer');
	}

	public function edit($id)
	{
		if (!$this->_check_admin()) return;

		$this->load->library('form_validation');
		$this->form_validation->set_rules('date_s', '日時', 'required');

		if ($this->form_validation->run() === FALSE) {
			$data['title'] = '募集編集';
			$data['breadcrumb'] = '募集一覧 &gt; 編集';
			$data['recruit'] = $this->recruit_admin_model->get_recruit_by_id($id);
			if (empty($data['recruit'])) {
				show_404();
			}
			$this->load->view('templates/header', $data);
			$this->load->view('gd_admin/edit', $data);
			$this->load->view('templates/footer');
		} else {
			$update_data = [
				'date_s' => $this->input->post('date_s'),
				'place' => $this->input->post('place'),
				'max_people' => $this->input->post('max_people'),
				'message' => $this->input->post('message'),
				'mentor_needed' => $this->input->post('mentor_needed') ? 1 : 0,
				'industry' => $this->input->post('industry'),
				'participants' => $this->input->post('participants')
			];
			$this->recruit_admin_model->update_recruit($id, $update_data);
			redirect('gd_admin');
		}
	}
	
	// (delete, settings 以下のメソッドは変更なしのため省略)
	// ...
}