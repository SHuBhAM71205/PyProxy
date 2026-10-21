#include <functional>
#include "proxy.h"
#include <iostream>
#include <fstream>
#include <thread>
#include <sstream>
#include <algorithm>
#include <windows.h>
#include <thread>
#include <stop_token>
// g++ -std=c++20 main.cpp proxy.cpp -o proxy.exe -lws2_32
std::string normalizeHost(const std::string &host)
{
    std::string normalized = host;
    std::transform(normalized.begin(), normalized.end(), normalized.begin(), ::tolower);

    // Remove www. if present
    if (normalized.find("www.") == 0)
    {
        normalized = normalized.substr(4);
    }

    return normalized;
}

ProxyServer::ProxyServer(int port) : port(port)
{
    WSADATA wsaData;
    WSAStartup(MAKEWORD(2, 2), &wsaData);

    serverSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    sockaddr_in serverAddr{};
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(port);
    serverAddr.sin_addr.s_addr = INADDR_ANY;

    bind(serverSocket, (sockaddr *)&serverAddr, sizeof(serverAddr));
    listen(serverSocket, SOMAXCONN);
    std::cout << "Proxy server started on port " << port << std::endl;

    loadRestrictedSites();
}

void ProxyServer::loadRestrictedSites()
{
    std::ifstream file("restricted.txt");
    std::string line;
    while (std::getline(file, line))
    {
        if (!line.empty())
        {
            restrictedSites.insert(normalizeHost(line));
        }
    }
}

ProxyServer::~ProxyServer()
{
    closesocket(serverSocket);
    WSACleanup();
}

void ProxyServer::_main_loop_thread_fn(std::stop_token stop_token)
{
    while (!stop_token.stop_requested())
    {
        SOCKET clientSocket = accept(serverSocket, nullptr, nullptr);
        if (clientSocket == INVALID_SOCKET)
        {
            std::cout << "msin_loop_thread_func" << std::endl;
        }

        std::thread(&ProxyServer::handleClient, this, clientSocket).detach();
    }
}
void ProxyServer::start()
{
    server_thread = std::jthread([this](std::stop_token st) {
        this->_main_loop_thread_fn(st);
    });
}

// Standard Structure for HTTPs request

// CONNECT www.example.com:443 HTTP/1.1
// Host: www.example.com:443
// User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36

// Standard Structure for HTTP request
// POST /submit-form HTTP/1.1
// Host: www.example.com
// User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36
// Accept: application/json
// Content-Type: application/x-www-form-urlencoded
// Content-Length: 27
// name=John&age=30

void ProxyServer::handleClient(SOCKET clientSocket)
{
    auto emitEvent = [this](const std::string &name, int value)
    {
        if (nec)
        {
            nec(name, value);
        }
    };

    emitEvent("clientinc", 1);
    char buffer[8192];
    int received = recv(clientSocket, buffer, sizeof(buffer), 0);
    if (received <= 0)
    {
        closesocket(clientSocket);
        emitEvent("clientdec", 1);
        return;
    }

    std::string request(buffer, received);
    emitEvent("total_requests", 1);
    std::string host;

    // Check if it's a CONNECT request (for HTTPS)
    if (request.substr(0, 7) == "CONNECT")
    {

        // Extract the host and port from CONNECT request
        size_t hostStart = request.find(" ") + 1;
        size_t hostEnd = request.find(" ", hostStart);
        std::string hostPort = request.substr(hostStart, hostEnd - hostStart);
        host = hostPort.substr(0, hostPort.find(":"));

        // Normalize and check if the host is restricted
        bool restricted = isRestricted(host);
        logRequest(host, restricted); // Log request

        if (restricted)
        {
            std::string response = "HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n";
            send(clientSocket, response.c_str(), response.size(), 0);
            emitEvent("blocked_requests", 1);
            std::cout << std::endl
                      << "--BLOCKED HTTPS REQUEST--" << std::endl
                      << host << "\n";
            closesocket(clientSocket);
            emitEvent("clientdec", 1);
            return;
        }

        // If not restricted, proceed with tunneling
        int port = std::stoi(hostPort.substr(hostPort.find(":") + 1));
        emitEvent("forwarded_requests", 1);
        tunnelHTTPS(clientSocket, host, port);
    }
    else
    {
        // Process HTTP requests
        size_t hostPos = request.find("Host: ");
        if (hostPos != std::string::npos)
        {
            size_t hostEnd = request.find("\r\n", hostPos);
            host = request.substr(hostPos + 6, hostEnd - hostPos - 6);

            // Normalize and check if the host is restricted
            bool restricted = isRestricted(host);
            logRequest(host, restricted); // Log request

            if (restricted)
            {
                // Block the request by sending 403 Forbidden
                std::string response = "HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n";
                send(clientSocket, response.c_str(), response.size(), 0);
                emitEvent("blocked_requests", 1);
                std::cout << std::endl
                          << "--BLOCKED HTTP REQUEST--" << std::endl
                          << host << std::endl;
                closesocket(clientSocket);
                emitEvent("clientdec", 1);
                return;
            }

            // If not restricted, forward the HTTP request
            emitEvent("forwarded_requests", 1);
            forwardHTTP(clientSocket, request);
        }
    }

    closesocket(clientSocket); // Close the client socket after handling

    emitEvent("clientdec", 1);
}

void ProxyServer::logRequest(const std::string &data, bool restricted)
{
    std::ofstream log(restricted ? "restricted_log.txt" : "proxy_log.txt", std::ios::app);

    if (restricted)
    {
        log << "--BLOCKED--" << std::endl
            << data << std::endl
            << std::endl;
        HANDLE hConsole = GetStdHandle(STD_OUTPUT_HANDLE);
        SetConsoleTextAttribute(hConsole, FOREGROUND_RED | FOREGROUND_INTENSITY);
        std::cout << "--BLOCKED--" << std::endl
                  << data << std::endl
                  << std::endl;
        SetConsoleTextAttribute(hConsole, FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE);
    }
    else
    {
        log << "--LOG--" << std::endl
            << data << std::endl
            << std::endl;
    }
    log.close();
}

void ProxyServer::tunnelHTTPS(SOCKET clientSocket, const std::string &host, int port)
{
    SOCKET remoteSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (remoteSocket == INVALID_SOCKET)
    {
        if (nec)
            nec("errors", 1);
        return;
    }
    sockaddr_in remoteAddr{};
    remoteAddr.sin_family = AF_INET;
    remoteAddr.sin_port = htons(port);

    hostent *he = gethostbyname(host.c_str());
    if (!he)
    {
        if (nec)
            nec("errors", 1);
        closesocket(remoteSocket);
        return;
    }
    memcpy(&remoteAddr.sin_addr, he->h_addr_list[0], he->h_length);

    if (connect(remoteSocket, (sockaddr *)&remoteAddr, sizeof(remoteAddr)) == SOCKET_ERROR)
    {
        if (nec)
            nec("errors", 1);
        closesocket(remoteSocket);
        return;
    }

    const char *ok = "HTTP/1.1 200 Connection Established\r\n\r\n";
    send(clientSocket, ok, strlen(ok), 0);

    auto relay = [](SOCKET src, SOCKET dst)
    {
        char buffer[4096];
        int len;
        while ((len = recv(src, buffer, sizeof(buffer), 0)) > 0)
        {
            send(dst, buffer, len, 0);
        }
    };

    std::thread t1(relay, clientSocket, remoteSocket);
    std::thread t2(relay, remoteSocket, clientSocket);

    t1.join();
    t2.join();

    closesocket(remoteSocket);
}

void ProxyServer::forwardHTTP(SOCKET clientSocket, const std::string &request)
{
    size_t hostPos = request.find("Host: ");
    if (hostPos == std::string::npos)
        return;

    size_t hostEnd = request.find("\r\n", hostPos);
    std::string host = request.substr(hostPos + 6, hostEnd - hostPos - 6);

    SOCKET remoteSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (remoteSocket == INVALID_SOCKET)
    {
        if (nec)
            nec("errors", 1);
        return;
    }
    sockaddr_in remoteAddr{};
    remoteAddr.sin_family = AF_INET;
    remoteAddr.sin_port = htons(80);

    hostent *he = gethostbyname(host.c_str());
    if (!he)
    {
        if (nec)
            nec("errors", 1);
        closesocket(remoteSocket);
        return;
    }
    memcpy(&remoteAddr.sin_addr, he->h_addr_list[0], he->h_length);

    if (connect(remoteSocket, (sockaddr *)&remoteAddr, sizeof(remoteAddr)) == SOCKET_ERROR)
    {
        if (nec)
            nec("errors", 1);
        closesocket(remoteSocket);
        return;
    }

    send(remoteSocket, request.c_str(), request.size(), 0);

    char buffer[8192];
    int len;
    while ((len = recv(remoteSocket, buffer, sizeof(buffer), 0)) > 0)
    {
        std::string response(buffer, len);
        std::cout << "--RESPONSE CHUNK--" << std::endl
                  << response << std::endl;
        send(clientSocket, buffer, len, 0);
    }

    closesocket(remoteSocket);
}

bool ProxyServer::isRestricted(const std::string &host)
{
    std::string normalized = normalizeHost(host);
    for (const auto &keyword : restrictedSites)
    {
        if (normalized.find(keyword) != std::string::npos)
        {
            return true;
        }
    }
    return false;
}


bool ProxyServer::addRestrictedSites(std::string host)
{
    std::string normalised_host = normalizeHost(host);
    return restrictedSites.insert(normalised_host).second;       
}
bool ProxyServer::removeRestrictedSites(std::string host)
{
    if (restrictedSites.erase(normalizeHost(host))){
        return true;
    }
    return false;
}

std::set<std::string> ProxyServer::getRestrictedSites(){

    return restrictedSites;
}

void ProxyServer::stop()
{
    server_thread.request_stop();

    if (serverSocket != INVALID_SOCKET)
    {
        closesocket(serverSocket);
        serverSocket = INVALID_SOCKET;
    }

    if (server_thread.joinable())
    {
        server_thread.join();
    }

    std::cout << "Proxy server stopped cleanly." << std::endl;

}

void ProxyServer::restart()
{
    std::cout << "Restarting proxy server..." << std::endl;
    stop();
    start();
    return;
}


void ProxyServer::setnamedEventCallback(namedEventCallback nec)
{
    this->nec = std::move(nec);
}