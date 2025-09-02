<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Gd_admin extends CI_Controller {

	public function __construct()
	{
		parent::__construct();
		// 必要なライブラリやモデルをロード
		$this->load->model('recruit_admin_model');
		$this->load->helper(array('url', 'form', 'download'));
		$this->load->library(array('form_validation', 'session'));

		// .envファイルからDiscord Botのトークンを読み込む
		$dotenv = Dotenv\Dotenv::createImmutable(FCPATH . '../../');
		$dotenv->load();
	}
    
    /**
	 * ダッシュボード（TOPページ）
	 */
	public function index()
	{
		$data['title'] = 'ダッシュボード';
		$this->load->view('templates/header', $data);
		$this->load->view('gd_admin/dashboard', $data);
		$this->load->view('templates/footer');
	}

	/**
	 * 募集一覧ページ
	 */
	public function list()
	{
		$data['title'] = '募集一覧';
		$recruits = $this->recruit_admin_model->get_all_recruits();
		
		// 参加者とメンターのIDを全件収集
		$user_ids = [];
		foreach ($recruits as $recruit) {
			$p_ids = json_decode($recruit['participants'], true);
			if (is_array($p_ids)) {
				$user_ids = array_merge($user_ids, $p_ids);
			}
			$m_ids = json_decode($recruit['mentors'], true);
			if (is_array($m_ids)) {
				$user_ids = array_merge($user_ids, $m_ids);
			}
		}
		$user_ids = array_unique($user_ids);

		// ユーザー名を取得
		$data['users'] = $this->recruit_admin_model->get_usernames_by_ids($user_ids);
		$data['recruits'] = $recruits;

		$this->load->view('templates/header', $data);
		$this->load->view('gd_admin/list', $data);
		$this->load->view('templates/footer');
	}

	/**
	 * 募集編集ページ
	 */
	public function edit($id)
	{
		// フォームのバリデーションルールを設定
		$this->form_validation->set_rules('date_s', '日時', 'required');
		$this->form_validation->set_rules('place', '場所', 'required');
		$this->form_validation->set_rules('max_people', '最大人数', 'required|integer');
		
		if ($this->form_validation->run() === FALSE) {
			$data['title'] = '募集編集';
			$data['recruit'] = $this->recruit_admin_model->get_recruit_by_id($id);
			if (empty($data['recruit'])) {
				show_404();
			}
			$this->load->view('templates/header', $data);
			$this->load->view('gd_admin/edit', $data);
			$this->load->view('templates/footer');
		} else {
			// participants と mentors をカンマ区切りの文字列から配列に変換
			$participants = empty($this->input->post('participants')) ? [] : explode(',', $this->input->post('participants'));
			$mentors = empty($this->input->post('mentors')) ? [] : explode(',', $this->input->post('mentors'));

			$update_data = array(
				'date_s' => $this->input->post('date_s'),
				'place' => $this->input->post('place'),
				'max_people' => $this->input->post('max_people'),
				'message' => $this->input->post('message'),
				'mentor_needed' => $this->input->post('mentor_needed') ? 1 : 0,
				'industry' => $this->input->post('industry'),
				'participants' => json_encode(array_map('trim', $participants)),
				'mentors' => json_encode(array_map('trim', $mentors)),
				'notification_sent' => $this->input->post('notification_sent') ? 1 : 0,
			);
			$this->recruit_admin_model->update_recruit($id, $update_data);
			$this->session->set_flashdata('success', '募集情報が更新されました。');
			redirect('gd_admin/list');
		}
	}

	/**
	 * 募集削除処理
	 */
	public function delete($id)
	{
		$this->recruit_admin_model->delete_recruit($id);
		$this->session->set_flashdata('success', '募集が削除されました。');
		redirect('gd_admin/list');
	}

	/**
	 * 設定ページ
	 */
	public function settings()
	{
		if ($this->input->post()) {
			$mentor_role_id = $this->input->post('mentor_role_id');
			$this->recruit_admin_model->set_setting('mentor_role_id', $mentor_role_id);
			$this->session->set_flashdata('success', '設定が保存されました。');
			redirect('gd_admin/settings');
		}
		
		$setting = $this->recruit_admin_model->get_setting('mentor_role_id');
		$data['mentor_role_id'] = $setting ? $setting['value'] : '';
		$data['title'] = '設定';

		$this->load->view('templates/header', $data);
		$this->load->view('gd_admin/settings', $data);
		$this->load->view('templates/footer');
	}
	
	/**
	 * ログ表示ページ
	 */
	public function logs()
	{
		$data['title'] = '操作ログ';
		$data['logs'] = $this->recruit_admin_model->get_all_logs();
		$this->load->view('templates/header', $data);
		$this->load->view('gd_admin/logs', $data);
		$this->load->view('templates/footer');
	}

	/**
	 * Discordユーザー情報を取得・更新する
	 */
	public function fetch_discord_users()
	{
		$user_ids_str = $this->input->get('ids');
		if (empty($user_ids_str)) {
			$this->output->set_content_type('application/json')->set_output(json_encode(['error' => 'No IDs provided']));
			return;
		}

		$user_ids = array_unique(explode(',', $user_ids_str));
		$token = $_ENV['DISCORD_BOT_TOKEN'];
		$users_data = [];

		foreach($user_ids as $id) {
			if (empty($id)) continue;
			
			// APIからユーザー情報を取得
			$url = "https://discord.com/api/v9/users/{$id}";
			$ch = curl_init();
			curl_setopt($ch, CURLOPT_URL, $url);
			curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
			curl_setopt($ch, CURLOPT_HTTPHEADER, ["Authorization: Bot {$token}"]);
			$response = curl_exec($ch);
			curl_close($ch);
			
			$user = json_decode($response, true);
			if (isset($user['username'])) {
				// 取得した情報をDBに保存
				$this->recruit_admin_model->store_user_info($id, $user['username']);
				$users_data[$id] = $user['username'];
			}
		}

		$this->output->set_content_type('application/json')->set_output(json_encode($users_data));
	}
}