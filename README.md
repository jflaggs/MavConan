# MavConan
Conan recipie files for creating a conan package from MAVSDK source. 

### Summary 

The `main` branch successfully packages a much older version of [MAVSDK](https://github.com/mavlink/MAVSDK). I did this by modifying [sintef-ocean's](https://github.com/sintef-ocean/conan-mavsdk) golden conanfile for a much older version of MAVSDK.

While attempting to bring the package to the latest version [v3.15.0](https://github.com/mavlink/MAVSDK/releases/tag/v3.15.0), it seems as though at some point MAVSDK stopped integrating with conan altogether. This could either be a legitamate issue OR due to lack of experience with conan on my part. 

### Future Work

At this point, the two options I see are:

1. Try to force conan to package the latest MAVSDK. 
2. Do a sort of "binary search" to find the last version that integrated with conan. 
3. A combination of 1 and 2; i.e. bring the conanfile to the latest version possible and then try to bring it up to date thereafter. 
4. I sense that there may be another, much more manual option available. 

I spent substantial time on Path 1 without much success (see `branch-whack-a-mole`). So I would try path 2 next if it is actually feasible to work with an older version of MAVSDK. 

## License

This project is licensed under MIT License [LICENSE.md](LICENSE.md).

## References
This readme.md was created with the help of [Markdown Live Preview](https://markdownlivepreview.com/).
