#include <mavsdk.h>
#include <iostream>

int main()
{
    mavsdk::Mavsdk mavsdk;
    std::string version = mavsdk.version();
	
	// std::string line;
    // std::getline(std::cin, line);
	std::cin.get(); 
    
	return 0;
}