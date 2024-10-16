-- SQL for creating the meta_class_data table
CREATE TABLE meta_class_data (
    class_id INT AUTO_INCREMENT PRIMARY KEY,
    class_label VARCHAR(191) NOT NULL,
    class_table_name VARCHAR(191) UNIQUE NOT NULL,
    class_file_id VARCHAR(191) UNIQUE NOT NULL,
    dep_name INT NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- SQL for creating the student_class_mapping table
CREATE TABLE student_class_mapping (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reg_number VARCHAR(191) NOT NULL,
    class_id INT NOT NULL,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES meta_class_data(class_id) ON DELETE CASCADE
);
