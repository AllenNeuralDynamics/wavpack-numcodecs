sudo apt update
sudo apt install wget
sudo apt install -y gettext

wget https://www.wavpack.com/wavpack-5.7.0.tar.bz2
tar -xf wavpack-5.7.0.tar.bz2
cd wavpack-5.7.0
./configure
sudo make install
cd ..