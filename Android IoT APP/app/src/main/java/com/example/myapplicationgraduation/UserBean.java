package com.example.myapplicationgraduation;

public class UserBean {
    private String account;
    private String password;
    private String device_key;

    public UserBean(String account, String password, String device_key) {
        this.account = account;
        this.password = password;
        this.device_key = device_key;
    }

    public String getAccount() {
        return account;
    }

    public void setAccount(String account) {
        this.account = account;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getDevice_Key() {
        return device_key;
    }

    public void setDevice_key(String device_key) {
        this.device_key = device_key;
    }

    @Override
    public String toString() {
        return "{" +
                "account='" + account + '\'' +
                ", password='" + password + '\'' +
                ", device_key='" + device_key + '\'' +
                "}";
    }
}
