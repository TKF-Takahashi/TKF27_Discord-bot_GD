<?php
class Auth_model extends CI_Model {

    private $db_bot;

    public function __construct()
    {
        parent::__construct();
        $this->db_bot = $this->load->database('bot_db', TRUE);
    }

    public function login($username, $password)
    {
        // [修正] 'admin' という固定値だった部分を、引数の $username 変数に修正
        $this->db_bot->where('username', $username);
        $query = $this->db_bot->get('administrators');
        
        if ($query->num_rows() == 1) {
            $user = $query->row_array();
            if (password_verify($password, $user['password'])) {
                return $user;
            }
        }
        return false;
    }
}