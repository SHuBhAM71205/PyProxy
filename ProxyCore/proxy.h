#pragma once
#include <winsock2.h>
#include <functional>
#include <string>
#include<set>
#include<thread>
#include<stop_token>
#pragma comment(lib, "ws2_32.lib")

class ProxyServer {
public:
    using namedEventCallback = std::function<void(const std::string&,const int&)>;

    ProxyServer(int port);
    ~ProxyServer();
    void start();
    bool addRestrictedSites(std::string host);
    bool removeRestrictedSites(std::string host);
    std::set<std::string> getRestrictedSites();
    void stop();
    void restart();
    void setnamedEventCallback(namedEventCallback nec);
    
    private:
    namedEventCallback nec;
    int port;
    std::jthread server_thread;
    SOCKET serverSocket;
    std::set<std::string> restrictedSites;
    void _main_loop_thread_fn(std::stop_token stop_token);
    void loadRestrictedSites();
    void handleClient(SOCKET clientSocket);
    void logRequest(const std::string& data, bool restricted);
    void tunnelHTTPS(SOCKET clientSocket, const std::string& host, int port);
    void forwardHTTP(SOCKET clientSocket, const std::string& request);
    bool isRestricted(const std::string& host);
};
