CREATE TABLE IF NOT EXISTS sys_user (
  user_id BIGINT NOT NULL AUTO_INCREMENT,
  username VARCHAR(64) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('admin', 'teacher', 'student') NOT NULL,
  student_id VARCHAR(50) DEFAULT NULL,
  course_id VARCHAR(50) DEFAULT NULL,
  is_active TINYINT DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  UNIQUE KEY uk_username (username),
  KEY idx_role (role),
  KEY idx_student_id (student_id),
  KEY idx_course_id (course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sys_login_log (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  username VARCHAR(64) NOT NULL,
  login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  login_ip VARCHAR(64) DEFAULT NULL,
  PRIMARY KEY (id),
  KEY idx_user_id (user_id),
  KEY idx_login_time (login_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sys_intervention (
  id BIGINT NOT NULL AUTO_INCREMENT,
  student_id VARCHAR(50) NOT NULL,
  course_id VARCHAR(50) DEFAULT NULL,
  warning_level VARCHAR(20) DEFAULT NULL,
  note TEXT NOT NULL,
  operator VARCHAR(64) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_student_id (student_id),
  KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
