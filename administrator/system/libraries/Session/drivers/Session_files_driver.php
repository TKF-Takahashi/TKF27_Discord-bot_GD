<?php
/**
 * CodeIgniter
 *
 * An open source application development framework for PHP
 *
 * This content is released under the MIT License (MIT)
 *
 * Copyright (c) 2014 - 2019, British Columbia Institute of Technology
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 * @package	CodeIgniter
 * @author	EllisLab Dev Team
 * @copyright	Copyright (c) 2008 - 2014, EllisLab, Inc. (https://ellislab.com/)
 * @copyright	Copyright (c) 2014 - 2019, British Columbia Institute of Technology (https://bcit.ca/)
 * @license	https://opensource.org/licenses/MIT	MIT License
 * @link	https://codeigniter.com
 * @since	Version 2.0.0
 * @filesource
 */
defined('BASEPATH') OR exit('No direct script access allowed');

/**
 * CodeIgniter Session Files Driver
 *
 * @package	CodeIgniter
 * @subpackage	Libraries
 * @category	Sessions
 * @author	Andrey Andreev
 * @link	https://codeigniter.com/user_guide/libraries/sessions.html
 */
class CI_Session_files_driver extends CI_Session_driver implements SessionHandlerInterface {

	/**
	 * Save path
	 *
	 * @var	string
	 */
	protected $_save_path;

	/**
	 * File handle
	 *
	 * @var	resource
	 */
	protected $_file_handle;

	/**
	 * File name
	 *
	 * @var	resource
	 */
	protected $_file_path;

	/**
	 * File new flag
	 *
	 * @var	bool
	 */
	protected $_file_new;

	// ------------------------------------------------------------------------

	/**
	 * Class constructor
	 *
	 * @param	array	$params	Configuration parameters
	 * @return	void
	 */
	public function __construct(&$params)
	{
		parent::__construct($params);

        // ▼▼▼▼▼▼▼▼▼ デバッグコード ▼▼▼▼▼▼▼▼▼
        log_message('debug', 'SESSION_DRIVER_CONFIG: Initializing with config: ' . print_r($this->_config, TRUE));
        // ▲▲▲▲▲▲▲▲▲ デバッグコード ▲▲▲▲▲▲▲▲▲

		if (isset($this->_config['save_path']))
		{
			$this->_save_path = $this->_config['save_path'];
		}
		else
		{
            // Fallback to php.ini setting
			$this->_save_path = config_item('sess_save_path');
            log_message('debug', 'SESSION_DRIVER_CONFIG: save_path not found in config, falling back to ini value: ' . $this->_save_path);
		}
	}

	// ------------------------------------------------------------------------

	/**
	 * Open
	 *
	 * Sanitizes the save_path directory.
	 *
	 * @param	string	$save_path	Path to session files' directory
	 * @param	string	$name		Session cookie name
	 * @return	bool
	 */
	public function open($save_path, $name)
	{
		if ( ! is_dir($save_path))
		{
			if ( ! mkdir($save_path, 0700, TRUE))
			{
				throw new Exception("Session: Configured save path '".$this->_save_path."' is not a directory, doesn't exist or cannot be created.");
			}
		}
		elseif ( ! is_writable($save_path))
		{
			throw new Exception("Session: Configured save path '".$this->_save_path."' is not writable by the PHP process.");
		}

		$this->_config['save_path'] = $save_path;
		$this->_file_path = $this->_config['save_path'].DIRECTORY_SEPARATOR
			.$name.($this->_config['match_ip'] ? md5($_SERVER['REMOTE_ADDR']) : '');

		return $this->_success;
	}

	// ------------------------------------------------------------------------

	/**
	 * Read
	 *
	 * Reads session data and acquires a lock
	 *
	 * @param	string	$session_id	Session ID
	 * @return	string	Serialized session data
	 */
	public function read($session_id)
	{
		// This is the only session driver that doesn't need to acquire a lock.
		// A lock is acquired and released on write(), as that's the only time
		// when a race condition can occur with this driver.
		$this->_file_new = ! file_exists($this->_file_path.$session_id);

		return ($this->_file_new)
			? ''
			: (string) file_get_contents($this->_file_path.$session_id);
	}

	// ------------------------------------------------------------------------

	/**
	 * Write
	 *
	 * Writes session data
	 *
	 * @param	string	$session_id	Session ID
	 * @param	string	$session_data	Serialized session data
	 * @return	bool
	 */
	public function write($session_id, $session_data)
	{
		$file_path = $this->_file_path.$session_id;
		if ( ! is_resource($this->_file_handle))
		{
			if (($this->_file_handle = fopen($file_path, 'c+b')) === FALSE)
			{
				log_message('error', "Session: Unable to open file '".$file_path."'.");
				return $this->_fail;
			}
		}

		// Prevent everybody else from reading/writing to the file for the next 30 seconds
		if (flock($this->_file_handle, LOCK_EX) === FALSE)
		{
			log_message('error', "Session: Unable to obtain lock for file '".$file_path."'.");
			fclose($this->_file_handle);
			$this->_file_handle = NULL;
			return $this->_fail;
		}

		// Erase the file's current contents and write the new data
		ftruncate($this->_file_handle, 0);
		rewind($this->_file_handle);
		if (($bytes = fwrite($this->_file_handle, $session_data)) > 0)
		{
			$this->_fingerprint = md5($session_data);
			return $this->_success;
		}

		return $this->_fail;
	}

	// ------------------------------------------------------------------------

	/**
	 * Close
	 *
	 * Releases locks and closes file descriptor.
	 *
	 * @return	bool
	 */
	public function close()
	{
		if (is_resource($this->_file_handle))
		{
			flock($this->_file_handle, LOCK_UN);
			fclose($this->_file_handle);
			$this->_file_handle = NULL;
			return $this->_success;
		}

		return $this->_success;
	}

	// ------------------------------------------------------------------------

	/**
	 * Destroy
	 *
	 * Destroys the current session.
	 *
	 * @param	string	$session_id	Session ID
	 * @return	bool
	 */
	public function destroy($session_id)
	{
		if ($this->close() === $this->_success)
		{
			if (file_exists($this->_file_path.$session_id))
			{
				if ( ! unlink($this->_file_path.$session_id))
				{
					log_message('error', 'Session: Unable to unlink session file '.$this->_file_path.$session_id);
					return $this->_fail;
				}
			}

			return $this->_success;
		}

		return $this->_fail;
	}

	// ------------------------------------------------------------------------

	/**
	 * Garbage Collector
	 *
	 * Deletes expired session files
	 *
	 * @param	int 	$maxlifetime	Maximum lifetime of session in seconds
	 * @return	bool
	 */
	public function gc($maxlifetime)
	{
		if ( ! is_dir($this->_config['save_path']) OR ($directory = opendir($this->_config['save_path'])) === FALSE)
		{
			log_message('debug', "Session: Garbage collector couldn't list files under directory '".$this->_config['save_path']."'.");
			return $this->_fail;
		}

		$ts = time() - $maxlifetime;

		$pattern = ($this->_config['match_ip'] === TRUE)
			? '[0-9a-f]{32}'
			: '';

		$pattern = sprintf(
			'#\A%s'.$pattern.'%s\z#',
			preg_quote($this->_config['cookie_name'], '#'),
			'[0-9a-v]{'.(32 - strlen($this->_config['cookie_name'])).',32}'
		);

		while (($file = readdir($directory)) !== FALSE)
		{
			// If the filename doesn't match this pattern, it's either not a session file or is not ours
			if ( ! preg_match($pattern, $file)
				OR ! is_file($this->_config['save_path'].DIRECTORY_SEPARATOR.$file)
				OR ($mtime = filemtime($this->_config['save_path'].DIRECTORY_SEPARATOR.$file)) === FALSE
				OR $mtime > $ts)
			{
				continue;
			}

			unlink($this->_config['save_path'].DIRECTORY_SEPARATOR.$file);
		}

		closedir($directory);

		return $this->_success;
	}
}