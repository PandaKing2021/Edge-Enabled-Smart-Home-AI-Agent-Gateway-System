package com.example.myapplicationgraduation;

import android.os.Environment;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.Properties;

public class ConfigPropertiesEditor {
    File extDir = Environment.getExternalStorageDirectory();
    private String filePath = "config.properties"; // 配置文件路径

    public ConfigPropertiesEditor() {
        // 初始化配置文件路径
    }

    public void readProperties() {
        try (FileInputStream input = new FileInputStream(new File(filePath))) {
            Properties prop = new Properties();
            prop.load(input);
        } catch (IOException ex) {
            ex.printStackTrace();
        }
    }

    public void writeProperties(String key, String value) {
        try (FileOutputStream output = new FileOutputStream(new File(filePath))) {
            Properties prop = new Properties();
            prop.load(new FileInputStream(filePath));

            // 修改键值对
            prop.setProperty(key, value);

            // 保存修改后的配置文件
            prop.store(output, null);
        } catch (IOException ex) {
            ex.printStackTrace();
        }
    }
}

